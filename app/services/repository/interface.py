from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class RepositoryProvider(Protocol):
    root: Path
    is_valid: bool

    def list_files(
        self,
        path: str | Path | None = None,
        max_depth: int | None = None,
        max_files: int = 200,
    ) -> list[str]:
        ...

    def read_file(
        self,
        relative_path: str | Path,
        start_line: int | None = None,
        end_line: int | None = None,
        max_lines: int = 200,
    ) -> dict[str, Any]:
        ...

    def search(
        self,
        query: str,
        max_results: int = 50,
        context_lines: int = 2,
    ) -> list[dict[str, Any]]:
        ...

    def find_symbol(
        self,
        symbol: str,
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        ...

    def find_references(
        self,
        symbol: str,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        ...

    def get_tree(
        self,
        max_depth: int = 3,
        max_files: int = 100,
    ) -> str:
        ...
