from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Iterable

from app.config.settings import settings
from app.tools.repository.schemas import CodeChunk


LANGUAGE_BY_EXTENSION: dict[str, str] = {
    ".py": "python",

    ".js": "javascript",
    ".jsx": "javascript-react",
    ".mjs": "javascript",
    ".cjs": "javascript",

    ".ts": "typescript",
    ".tsx": "typescript-react",

    ".html": "html",
    ".htm": "html",

    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",

    ".java": "java",

    ".kt": "kotlin",
    ".kts": "kotlin",

    ".go": "go",

    ".rs": "rust",

    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",

    ".cs": "csharp",

    ".rb": "ruby",

    ".php": "php",

    ".swift": "swift",

    ".scala": "scala",

    ".sql": "sql",

    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",

    ".ps1": "powershell",

    ".yaml": "yaml",
    ".yml": "yaml",

    ".json": "json",

    ".md": "markdown",
    ".mdx": "mdx",
}


SPECIAL_FILES: dict[str, str] = {
    "dockerfile": "dockerfile",
    "makefile": "makefile",
}


class CodeChunkBuilder:
    """
    Builds semantic-search chunks from a repository.

    This Phase 2 implementation intentionally does not require
    Tree-sitter.

    It uses:
        - file/language detection
        - lightweight symbol detection
        - line-based chunking
        - overlapping chunks

    Tree-sitter can replace the symbol detection later without
    changing the Qdrant/embedding architecture.
    """

    def __init__(
        self,
        chunk_lines: int | None = None,
        overlap_lines: int | None = None,
        ignored_dirs: list[str] | None = None,
        max_files: int | None = None,
        max_file_size_kb: int | None = None,
    ) -> None:

        self.chunk_lines = (
            chunk_lines
            if chunk_lines is not None
            else settings.repository_chunk_lines
        )

        self.overlap_lines = (
            overlap_lines
            if overlap_lines is not None
            else settings.repository_chunk_overlap
        )

        self.ignored_dirs = set(
            ignored_dirs
            if ignored_dirs is not None
            else settings.repository_ignored_dirs
        )

        self.max_files = (
            max_files
            if max_files is not None
            else settings.repository_max_files
        )

        self.max_file_size_kb = (
            max_file_size_kb
            if max_file_size_kb is not None
            else settings.repository_max_file_size_kb
        )

        if self.chunk_lines <= 0:
            raise ValueError(
                "chunk_lines must be > 0"
            )

        if self.overlap_lines < 0:
            raise ValueError(
                "overlap_lines must be >= 0"
            )

        if self.overlap_lines >= self.chunk_lines:
            raise ValueError(
                "overlap_lines must be smaller "
                "than chunk_lines"
            )

    # ============================================================
    # Public
    # ============================================================

    def build(
        self,
        repository_root: str | Path,
        repository_id: str | None = None,
    ) -> list[CodeChunk]:

        root = Path(
            repository_root
        ).resolve()

        if not root.exists():
            raise FileNotFoundError(
                f"Repository does not exist: {root}"
            )

        if not root.is_dir():
            raise ValueError(
                f"Repository path is not a directory: {root}"
            )

        repo_id = (
            repository_id
            or self._repository_id(root)
        )

        chunks: list[CodeChunk] = []

        processed_files = 0

        for file_path in self._iter_files(root):

            if (
                self.max_files > 0
                and processed_files >= self.max_files
            ):
                break

            language = self.detect_language(
                file_path
            )

            if language is None:
                continue

            try:
                file_size_kb = (
                    file_path.stat().st_size / 1024
                )
            except OSError:
                continue

            if (
                self.max_file_size_kb > 0
                and file_size_kb
                > self.max_file_size_kb
            ):
                continue

            try:
                content = file_path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            except OSError:
                continue

            if not content.strip():
                continue

            processed_files += 1

            relative_path = (
                file_path
                .relative_to(root)
                .as_posix()
            )

            chunks.extend(
                self._chunk_file(
                    repository_id=repo_id,
                    relative_path=relative_path,
                    language=language,
                    content=content,
                )
            )

        return chunks

    # ============================================================
    # File discovery
    # ============================================================

    def _iter_files(
        self,
        root: Path,
    ) -> Iterable[Path]:

        count = 0

        for path in root.rglob("*"):

            if (
                self.max_files > 0
                and count >= self.max_files
            ):
                return

            if not path.is_file():
                continue

            relative_parts = (
                path.relative_to(root).parts
            )

            if any(
                part in self.ignored_dirs
                for part in relative_parts
            ):
                continue

            if self._looks_binary(path):
                continue

            count += 1

            yield path

    @staticmethod
    def _looks_binary(
        path: Path,
    ) -> bool:

        try:
            data = path.read_bytes()[:4096]
        except OSError:
            return True

        return b"\x00" in data

    # ============================================================
    # Language detection
    # ============================================================

    @staticmethod
    def detect_language(
        path: Path,
    ) -> str | None:

        filename = path.name.lower()

        if filename in SPECIAL_FILES:
            return SPECIAL_FILES[filename]

        return LANGUAGE_BY_EXTENSION.get(
            path.suffix.lower()
        )

    # ============================================================
    # File chunking
    # ============================================================

    def _chunk_file(
        self,
        repository_id: str,
        relative_path: str,
        language: str,
        content: str,
    ) -> list[CodeChunk]:

        lines = content.splitlines()

        if not lines:
            return []

        symbols = self._find_symbols(
            lines,
            language,
        )

        if symbols:
            return self._build_symbol_chunks(
                repository_id=repository_id,
                relative_path=relative_path,
                language=language,
                lines=lines,
                symbols=symbols,
            )

        return self._build_line_chunks(
            repository_id=repository_id,
            relative_path=relative_path,
            language=language,
            lines=lines,
        )

    # ============================================================
    # Symbol detection
    # ============================================================

    def _find_symbols(
        self,
        lines: list[str],
        language: str,
    ) -> list[tuple[int, str]]:

        patterns: list[
            re.Pattern[str]
        ] = []

        if language == "python":

            patterns = [
                re.compile(
                    r"^\s*(?:async\s+)?def\s+"
                    r"([A-Za-z_]\w*)"
                ),
                re.compile(
                    r"^\s*class\s+"
                    r"([A-Za-z_]\w*)"
                ),
            ]

        elif language in {
            "javascript",
            "javascript-react",
            "typescript",
            "typescript-react",
        }:

            patterns = [
                re.compile(
                    r"^\s*(?:export\s+)?"
                    r"(?:default\s+)?"
                    r"(?:async\s+)?function\s+"
                    r"([A-Za-z_$][\w$]*)"
                ),
                re.compile(
                    r"^\s*(?:export\s+)?"
                    r"(?:default\s+)?class\s+"
                    r"([A-Za-z_$][\w$]*)"
                ),
                re.compile(
                    r"^\s*(?:export\s+)?"
                    r"(?:const|let|var)\s+"
                    r"([A-Za-z_$][\w$]*)\s*="
                ),
                re.compile(
                    r"^\s*(?:export\s+)?"
                    r"(?:interface|type)\s+"
                    r"([A-Za-z_$][\w$]*)"
                ),
            ]

        elif language == "java":

            patterns = [
                re.compile(
                    r"^\s*(?:public|private|protected)?\s*"
                    r"(?:static\s+)?"
                    r"(?:class|interface|enum)\s+"
                    r"([A-Za-z_]\w*)"
                ),
            ]

        elif language == "go":

            patterns = [
                re.compile(
                    r"^\s*func\s+"
                    r"(?:\([^)]*\)\s*)?"
                    r"([A-Za-z_]\w*)\s*\("
                ),
                re.compile(
                    r"^\s*type\s+"
                    r"([A-Za-z_]\w*)"
                ),
            ]

        elif language == "rust":

            patterns = [
                re.compile(
                    r"^\s*(?:pub\s+)?"
                    r"(?:async\s+)?fn\s+"
                    r"([A-Za-z_]\w*)"
                ),
                re.compile(
                    r"^\s*(?:pub\s+)?struct\s+"
                    r"([A-Za-z_]\w*)"
                ),
                re.compile(
                    r"^\s*(?:pub\s+)?enum\s+"
                    r"([A-Za-z_]\w*)"
                ),
                re.compile(
                    r"^\s*(?:pub\s+)?trait\s+"
                    r"([A-Za-z_]\w*)"
                ),
            ]

        else:
            return []

        matches: list[
            tuple[int, str]
        ] = []

        for index, line in enumerate(lines):

            for pattern in patterns:

                match = pattern.match(line)

                if match:

                    matches.append(
                        (
                            index,
                            match.group(1),
                        )
                    )

                    break

        return matches

    # ============================================================
    # Symbol chunks
    # ============================================================

    def _build_symbol_chunks(
        self,
        repository_id: str,
        relative_path: str,
        language: str,
        lines: list[str],
        symbols: list[tuple[int, str]],
    ) -> list[CodeChunk]:

        chunks: list[CodeChunk] = []

        for index, (
            start,
            symbol,
        ) in enumerate(symbols):

            if index + 1 < len(symbols):
                end = symbols[index + 1][0]
            else:
                end = len(lines)

            symbol_lines = lines[
                start:end
            ]

            if not symbol_lines:
                continue

            if len(symbol_lines) <= self.chunk_lines:

                chunks.append(
                    self._create_chunk(
                        repository_id=repository_id,
                        relative_path=relative_path,
                        language=language,
                        lines=symbol_lines,
                        start_line=start + 1,
                        chunk_index=len(chunks),
                        symbol=symbol,
                        chunk_type="symbol",
                    )
                )

            else:

                chunks.extend(
                    self._split_symbol(
                        repository_id=repository_id,
                        relative_path=relative_path,
                        language=language,
                        lines=symbol_lines,
                        absolute_start=start,
                        symbol=symbol,
                        existing_index=len(chunks),
                    )
                )

        return chunks

    def _split_symbol(
        self,
        repository_id: str,
        relative_path: str,
        language: str,
        lines: list[str],
        absolute_start: int,
        symbol: str,
        existing_index: int,
    ) -> list[CodeChunk]:

        chunks: list[CodeChunk] = []

        step = (
            self.chunk_lines
            - self.overlap_lines
        )

        index = 0

        while index < len(lines):

            end = min(
                index + self.chunk_lines,
                len(lines),
            )

            piece = lines[
                index:end
            ]

            chunks.append(
                self._create_chunk(
                    repository_id=repository_id,
                    relative_path=relative_path,
                    language=language,
                    lines=piece,
                    start_line=(
                        absolute_start
                        + index
                        + 1
                    ),
                    chunk_index=(
                        existing_index
                        + len(chunks)
                    ),
                    symbol=symbol,
                    chunk_type="symbol",
                )
            )

            if end >= len(lines):
                break

            index += step

        return chunks

    # ============================================================
    # Generic line chunks
    # ============================================================

    def _build_line_chunks(
        self,
        repository_id: str,
        relative_path: str,
        language: str,
        lines: list[str],
    ) -> list[CodeChunk]:

        chunks: list[CodeChunk] = []

        step = (
            self.chunk_lines
            - self.overlap_lines
        )

        index = 0

        while index < len(lines):

            end = min(
                index + self.chunk_lines,
                len(lines),
            )

            piece = lines[
                index:end
            ]

            chunks.append(
                self._create_chunk(
                    repository_id=repository_id,
                    relative_path=relative_path,
                    language=language,
                    lines=piece,
                    start_line=index + 1,
                    chunk_index=len(chunks),
                    symbol=None,
                    chunk_type="file_region",
                )
            )

            if end >= len(lines):
                break

            index += step

        return chunks

    # ============================================================
    # Create chunk
    # ============================================================

    @staticmethod
    def _create_chunk(
        repository_id: str,
        relative_path: str,
        language: str,
        lines: list[str],
        start_line: int,
        chunk_index: int,
        symbol: str | None,
        chunk_type: str,
    ) -> CodeChunk:

        content = "\n".join(lines)

        raw_id = (
            f"{repository_id}:"
            f"{relative_path}:"
            f"{start_line}:"
            f"{chunk_index}"
        )

        chunk_id = hashlib.sha1(
            raw_id.encode("utf-8")
        ).hexdigest()

        return CodeChunk(
            chunk_id=chunk_id,
            repository_id=repository_id,
            file_path=relative_path,
            language=language,
            content=content,
            start_line=start_line,
            end_line=(
                start_line
                + len(lines)
                - 1
            ),
            chunk_index=chunk_index,
            symbol=symbol,
            chunk_type=chunk_type,
        )

    @staticmethod
    def _repository_id(
        root: Path,
    ) -> str:

        return hashlib.sha1(
            str(root).encode("utf-8")
        ).hexdigest()[:16]
