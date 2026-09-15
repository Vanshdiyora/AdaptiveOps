from __future__ import annotations

from app.services.repository.local import LocalRepositoryProvider

from .indexer import IndexedSymbol, RepositoryIndex
from .schemas import CodeLocation


class RepositoryContextBuilder:

    def __init__(
        self,
        repository: LocalRepositoryProvider,
        index: RepositoryIndex,
        max_files: int = 10,
        max_symbols: int = 20,
        max_lines_per_symbol: int = 150,
    ) -> None:

        self.repository = repository
        self.index = index

        self.max_files = max_files
        self.max_symbols = max_symbols
        self.max_lines_per_symbol = (
            max_lines_per_symbol
        )

    async def location_for_symbol(
        self,
        symbol: IndexedSymbol,
        score: float = 0.0,
    ) -> CodeLocation:

        file_data = await self.index.get_file(
            symbol.file_path
        )

        code = ""

        if file_data:

            lines = file_data.text.splitlines()

            code = "\n".join(
                lines[
                    symbol.start_line - 1 :
                    symbol.end_line
                ][: self.max_lines_per_symbol]
            )

        return CodeLocation(
            file_path=symbol.file_path,
            start_line=symbol.start_line,
            end_line=min(
                symbol.end_line,
                symbol.start_line
                + self.max_lines_per_symbol
                - 1,
            ),
            symbol_name=(
                symbol.qualified_name
                or symbol.name
            ),
            symbol_type=symbol.symbol_type,
            code=code,
            score=score,
        )

    async def surrounding_location(
        self,
        file_path: str,
        line_number: int,
        score: float = 0.0,
    ) -> CodeLocation | None:

        symbol = await self.index.find_symbol_containing_line(
            file_path,
            line_number,
        )

        if symbol:

            return await self.location_for_symbol(
                symbol,
                score,
            )

        try:

            read_result = self.repository.read_file(
                file_path,
                start_line=max(
                    1,
                    line_number - 5,
                ),
                end_line=line_number + 5,
                max_lines=20,
            )

        except (
            OSError,
            ValueError,
        ):

            return None

        return CodeLocation(
            file_path=read_result["file"],
            start_line=read_result["start_line"],
            end_line=read_result["end_line"],
            code=read_result["snippet"],
            score=score,
        )