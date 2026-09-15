from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LocalRepositoryProvider:
    DEFAULT_IGNORED_DIRS = {
        ".git",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".venv",
        "venv",
        "dist",
        "build",
        ".next",
        "coverage",
        "target",
        "vendor",
        ".idea",
        ".vscode",
    }

    SENSITIVE_NAMES = {
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        "credentials",
        "credentials.json",
        "secrets",
        "secrets.json",
        "id_rsa",
    }
    SENSITIVE_SUFFIXES = (".pem", ".key", ".p12", ".pfx")

    def __init__(
        self,
        root: str | Path,
        ignored_dirs: set[str] | None = None,
        max_file_size_kb: int = 256,
        max_files: int = 200,
        max_search_results: int = 50,
    ):
        self.root = Path(root).expanduser().resolve()
        self.ignored_dirs = set(ignored_dirs or self.DEFAULT_IGNORED_DIRS)
        self.max_file_size_kb = max_file_size_kb
        self.max_files = max_files
        self.max_search_results = max_search_results

        self._validate_root()

    @property
    def is_valid(self) -> bool:
        return self.root.exists() and self.root.is_dir()

    def _validate_root(self) -> None:
        if not self.root.exists():
            raise ValueError(f"Repository path does not exist: {self.root}")
        if not self.root.is_dir():
            raise ValueError(f"Repository path is not a directory: {self.root}")
        logger.info("[Repository] Initialized: %s", self.root)

    def _is_ignored(self, relative_path: Path) -> bool:
        return any(part in self.ignored_dirs for part in relative_path.parts)

    @classmethod
    def _is_sensitive(cls, relative_path: Path) -> bool:
        name = relative_path.name.lower()
        return (
            name in cls.SENSITIVE_NAMES
            or name.endswith(cls.SENSITIVE_SUFFIXES)
        )

    def _resolve_relative_path(self, relative_path: str | Path) -> Path:
        candidate = Path(relative_path)
        if candidate.is_absolute():
            raise ValueError("Absolute paths are not allowed inside the repository provider.")
        resolved = (self.root / candidate).resolve(strict=False)
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Requested path is outside the repository root: {relative_path}") from exc
        return resolved

    def list_files(
        self,
        path: str | Path | None = None,
        max_depth: int | None = None,
        max_files: int = 200,
    ) -> list[str]:
        base = self.root if path is None else self._resolve_relative_path(path)
        if not base.exists() or not base.is_dir():
            raise ValueError(f"Invalid repository directory: {base}")

        collected: list[str] = []
        queue: list[tuple[Path, int]] = [(base, 0)]
        limit = min(max_files, self.max_files)

        while queue and len(collected) < limit:
            current, depth = queue.pop(0)
            if max_depth is not None and depth > max_depth:
                continue

            try:
                children = sorted(current.iterdir(), key=lambda item: item.name)
            except OSError:
                continue

            for child in children:
                if len(collected) >= limit:
                    break

                try:
                    relative = child.relative_to(self.root)
                except ValueError:
                    continue

                if self._is_ignored(relative) or self._is_sensitive(relative):
                    continue

                if child.is_dir():
                    if max_depth is None or depth < max_depth:
                        queue.append((child, depth + 1))
                    continue

                if not child.is_file():
                    continue

                if self._is_binary_file(child):
                    continue

                try:
                    child.read_bytes()
                except OSError:
                    continue

                collected.append(str(relative).replace('\\', '/'))

        return collected[:limit]

    def read_file(
        self,
        relative_path: str | Path,
        start_line: int | None = None,
        end_line: int | None = None,
        max_lines: int = 200,
    ) -> dict[str, Any]:
        resolved = self._resolve_relative_path(relative_path)
        relative = resolved.relative_to(self.root)
        if self._is_sensitive(relative):
            raise ValueError(f"Sensitive repository files are not readable: {relative_path}")
        if not resolved.exists() or not resolved.is_file():
            raise FileNotFoundError(f"File not found inside repository: {relative_path}")
        if self._is_binary_file(resolved):
            raise ValueError(f"Binary files are not supported: {relative_path}")

        file_size_bytes = resolved.stat().st_size
        max_size_bytes = self.max_file_size_kb * 1024
        if file_size_bytes > max_size_bytes:
            raise ValueError(
                f"File exceeds the configured size limit: {relative_path} ({file_size_bytes} bytes)"
            )

        with resolved.open("r", encoding="utf-8", errors="strict") as handle:
            lines = handle.readlines()

        if not lines:
            return {
                "file": str(relative).replace('\\', '/'),
                "start_line": 1,
                "end_line": 0,
                "snippet": "",
                "line_count": 0,
            }

        requested_start = max(1, start_line or 1)
        requested_end = len(lines) if end_line is None else min(len(lines), max(1, end_line))
        start_index = max(0, requested_start - 1)
        end_index = max(start_index, requested_end)
        requested = lines[start_index:end_index]

        if max_lines is not None and max_lines > 0:
            requested = requested[:max_lines]

        if not requested:
            return {
                "file": str(relative).replace('\\', '/'),
                "start_line": requested_start,
                "end_line": requested_start - 1,
                "snippet": "",
                "line_count": len(lines),
            }

        actual_start = start_index + 1
        actual_end = min(len(lines), start_index + len(requested))
        snippet = "".join(requested).rstrip()
        return {
            "file": str(relative).replace('\\', '/'),
            "start_line": actual_start,
            "end_line": actual_end,
            "snippet": snippet,
            "line_count": len(lines),
        }

    def search(
        self,
        query: str,
        max_results: int = 50,
        context_lines: int = 2,
    ) -> list[dict[str, Any]]:
        if not query or not query.strip():
            raise ValueError("Repository search requires a non-empty query.")

        matches: list[dict[str, Any]] = []
        result_limit = min(max_results, self.max_search_results)
        normalized_query = query.strip()

        for path in self.list_files(max_files=self.max_files):
            full_path = self._resolve_relative_path(path)
            if self._is_binary_file(full_path):
                continue
            try:
                with full_path.open("r", encoding="utf-8", errors="ignore") as handle:
                    lines = handle.readlines()
            except (OSError, UnicodeError):
                continue

            for index, line in enumerate(lines, start=1):
                if normalized_query.lower() not in line.lower():
                    continue

                context_start = max(1, index - context_lines)
                context_end = min(len(lines), index + context_lines)
                snippet = "".join(lines[context_start - 1:context_end])
                matches.append(
                    {
                        "file": path,
                        "line": index,
                        "match": line.rstrip("\n\r"),
                        "context": snippet.rstrip(),
                        "context_start_line": context_start,
                        "context_end_line": context_end,
                    }
                )
                if len(matches) >= result_limit:
                    return matches

        return matches[:result_limit]

    def find_symbol(
        self,
        symbol: str,
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        if not symbol or not symbol.strip():
            raise ValueError("Symbol search requires a non-empty symbol.")
        escaped = symbol.strip()
        matches = self.search(escaped, max_results=max_results, context_lines=2)
        return [match for match in matches if escaped.lower() in match["match"].lower()]

    def find_references(
        self,
        symbol: str,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        return self.search(symbol, max_results=max_results, context_lines=1)

    def get_tree(
        self,
        max_depth: int = 3,
        max_files: int = 100,
    ) -> str:
        lines: list[str] = []

        def walk(directory: Path, prefix: str = "") -> None:
            if len(lines) >= max_files:
                return
            children = sorted(
                [child for child in directory.iterdir() if not self._is_ignored(child.relative_to(self.root))],
                key=lambda item: item.name,
            )
            for idx, child in enumerate(children):
                if len(lines) >= max_files:
                    return
                if child.is_dir():
                    is_last = idx == len(children) - 1
                    branch = "└── " if is_last else "├── "
                    lines.append(f"{prefix}{branch}{child.name}/")
                    if max_depth > 0:
                        walk(child, prefix + ("    " if is_last else "│   "),)
                elif child.is_file() and not self._is_binary_file(child):
                    is_last = idx == len(children) - 1
                    branch = "└── " if is_last else "├── "
                    lines.append(f"{prefix}{branch}{child.name}")

        walk(self.root)
        return "\n".join(lines) if lines else "."

    @staticmethod
    def _is_binary_file(path: Path) -> bool:
        if path.is_dir():
            return False
        try:
            with path.open("rb") as handle:
                chunk = handle.read(1024)
        except OSError:
            return True
        if not chunk:
            return False
        return b"\x00" in chunk
