from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.services.repository.local import LocalRepositoryProvider


@dataclass(slots=True)
class IndexedSymbol:
    file_path: str
    start_line: int
    end_line: int
    name: str
    qualified_name: str | None = None
    symbol_type: str = "function"


@dataclass(slots=True)
class IndexedFile:
    file_path: str
    text: str


class RepositoryIndex:
    """Lightweight symbol index used by repository investigation context."""

    def __init__(
        self,
        repository: LocalRepositoryProvider,
        *,
        max_files: int = 200,
    ) -> None:
        self.repository = repository
        self.max_files = max_files

    async def index_repository(self) -> dict[str, Any]:
        files = self.repository.list_files(max_files=self.max_files)
        return {
            "repository_path": str(self.repository.root),
            "files": len(files),
            "indexed_symbols": 0,
        }

    async def get_file(self, file_path: str) -> IndexedFile | None:
        try:
            file_data = self.repository.read_file(
                file_path,
                start_line=1,
                end_line=100000,
                max_lines=100000,
            )
        except (FileNotFoundError, OSError, ValueError):
            return None

        text = file_data.get("snippet", "")
        if not text and file_data.get("line_count", 0) == 0:
            return None

        if file_data.get("file") and text:
            return IndexedFile(file_path=file_data["file"], text=text)

        try:
            absolute = Path(self.repository.root, file_path).read_text(encoding="utf-8")
        except (OSError, ValueError):
            return None

        return IndexedFile(file_path=file_path, text=absolute)

    async def find_symbol_containing_line(
        self,
        file_path: str,
        line_number: int,
    ) -> IndexedSymbol | None:
        file_data = await self.get_file(file_path)
        if file_data is None:
            return None

        lines = file_data.text.splitlines()
        if not lines:
            return None

        target = max(1, min(int(line_number), len(lines)))
        for index in range(target, 0, -1):
            match = re.match(
                r"\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)",
                lines[index - 1],
            )
            if not match:
                continue

            name = match.group(1)
            symbol_type = "class" if lines[index - 1].strip().startswith("class") else "function"
            return IndexedSymbol(
                file_path=file_path,
                start_line=index,
                end_line=min(len(lines), index + 20),
                name=name,
                qualified_name=name,
                symbol_type=symbol_type,
            )

        return None

    async def find_symbol(self, symbol_name: str) -> list[IndexedSymbol]:
        if not symbol_name or not symbol_name.strip():
            return []

        symbol_name = symbol_name.strip()
        pattern = re.compile(rf"(?:async\s+)?(?:def|class)\s+{re.escape(symbol_name)}\b")
        results: list[IndexedSymbol] = []

        for file_path in self.repository.list_files(max_files=self.max_files):
            file_data = await self.get_file(file_path)
            if file_data is None:
                continue

            lines = file_data.text.splitlines()
            for index, line in enumerate(lines, start=1):
                match = pattern.search(line)
                if not match:
                    continue

                name = symbol_name
                symbol_type = "class" if line.strip().startswith("class") else "function"
                results.append(
                    IndexedSymbol(
                        file_path=file_path,
                        start_line=index,
                        end_line=min(len(lines), index + 10),
                        name=name,
                        qualified_name=name,
                        symbol_type=symbol_type,
                    )
                )

        return results

    async def find_callers(self, symbol: IndexedSymbol) -> list[IndexedSymbol]:
        return []

    async def find_callees(self, symbol: IndexedSymbol) -> list[IndexedSymbol]:
        return []


__all__ = ["IndexedSymbol", "RepositoryIndex"]
