from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.agents.observation.schemas import (
    ExceptionEntry,
    LogEntry,
    TraceEntry,
)
from app.config.settings import settings
from app.services.repository.local import (
    LocalRepositoryProvider,
)

from .context import RepositoryContextBuilder
from .indexer import RepositoryIndex
from .schemas import (
    CodeLocation,
    InvestigationSignal,
    RepositoryInvestigationResult,
    StackFrame,
)
from .search import HybridRepositorySearch
from .stacktrace import parse_stack_trace


logger = logging.getLogger(__name__)


class RepositoryInvestigationEngine:

    def __init__(
        self,
        repository_path: str | Path,
        *,
        ignored_dirs: set[str] | None = None,
        max_files: int = 500,
        max_results: int = 100,
        call_graph_depth: int = 2,
        max_context_files: int = 10,
        max_context_symbols: int = 20,
        max_lines_per_symbol: int = 150,
    ) -> None:

        self.repository = (
            LocalRepositoryProvider(
                repository_path,
                ignored_dirs=ignored_dirs,
                max_files=max_files,
                max_search_results=max_results,
            )
        )

        self.index = RepositoryIndex(
            self.repository,
            max_files=max_files,
        )

        self.search = HybridRepositorySearch(
            self.repository,
            self.index,
        )

        self.context = (
            RepositoryContextBuilder(
                self.repository,
                self.index,
                max_files=max_context_files,
                max_symbols=max_context_symbols,
                max_lines_per_symbol=max_lines_per_symbol,
            )
        )

        self.call_graph_depth = max(
            0,
            call_graph_depth,
        )

    async def investigate(
        self,
        exception: ExceptionEntry,
        traces: list[TraceEntry] | None = None,
        logs: list[LogEntry] | None = None,
    ) -> RepositoryInvestigationResult:

        try:

            await self.index.index_repository()

            signal = self._build_signal(
                exception,
                traces or [],
                logs or [],
            )

            logger.info(
                "[RepositoryInvestigation] "
                "exception=%s operation=%s "
                "frames=%d",
                signal.exception_type,
                signal.operation,
                len(signal.frames),
            )

            primary = await self._resolve_primary(
                signal
            )

            if primary is None:

                return self._result(
                    signal,
                    explanation=(
                        "No relevant repository "
                        "code found."
                    ),
                )

            primary_symbol = (
                await self.index
                .find_symbol_containing_line(
                    primary.file_path,
                    primary.start_line,
                )
            )

            callers: list[
                CodeLocation
            ] = []

            callees: list[
                CodeLocation
            ] = []

            if (
                primary_symbol
                and self.call_graph_depth > 0
            ):

                callers = (
                    await self._graph_locations(
                        primary_symbol,
                        direction="callers",
                    )
                )

                callees = (
                    await self._graph_locations(
                        primary_symbol,
                        direction="callees",
                    )
                )

            related = (
                await self._related_locations(
                    signal,
                    primary,
                )
            )

            return self._result(
                signal,
                primary_location=primary,
                related_locations=related,
                callers=callers,
                callees=callees,
                explanation=self._explanation(
                    primary,
                    callers,
                    callees,
                ),
            )

        except (
            OSError,
            RuntimeError,
            ValueError,
        ) as error:

            logger.exception(
                "[RepositoryInvestigation] failed"
            )

            return RepositoryInvestigationResult(
                exception_type=exception.exception_type,
                message=exception.message,
                operation=exception.operation,
                explanation=(
                    "Repository investigation "
                    f"failed safely: {error}"
                ),
            )

    def _build_signal(
        self,
        exception: ExceptionEntry,
        traces: list[TraceEntry],
        logs: list[LogEntry],
    ) -> InvestigationSignal:

        frames = parse_stack_trace(
            exception.stack_trace
        )

        operation = exception.operation

        if not operation and traces:

            operation = traces[0].operation

        identifiers = self._incident_identifiers(
            traces,
            logs,
        )

        return InvestigationSignal(
            exception_type=exception.exception_type,
            message=exception.message,
            operation=operation,
            frames=frames,
            identifiers=identifiers,
        )

    async def _resolve_primary(
        self,
        signal: InvestigationSignal,
    ) -> CodeLocation | None:

        # 1. Stack trace has highest confidence.
        for frame in signal.frames:

            location = await self._resolve_frame(
                frame
            )

            if location:
                return location

        # 2. Hybrid retrieval.
        results = await self.search.search(
            signal,
            limit=10,
            candidate_limit=50,
        )

        for result in results:

            location = (
                await self._resolve_search_result(
                    result
                )
            )

            if location:
                return location

        return None

    async def _resolve_frame(
        self,
        frame: StackFrame,
    ) -> CodeLocation | None:

        if (
            frame.file_path
            and frame.line_number
        ):

            safe_path = (
                self._safe_relative_path(
                    frame.file_path
                )
            )

            if safe_path:

                location = (
                    await self.context
                    .surrounding_location(
                        safe_path,
                        frame.line_number,
                        1.0,
                    )
                )

                if location:

                    if (
                        frame.function_name
                        and not location.symbol_name
                    ):
                        location.symbol_name = (
                            frame.function_name
                        )

                    return location

        if frame.function_name:

            symbols = (
                await self.index.find_symbol(
                    frame.function_name
                )
            )

            if symbols:

                return (
                    await self.context
                    .location_for_symbol(
                        symbols[0],
                        0.95,
                    )
                )

        return None

    async def _resolve_search_result(
        self,
        result: Any,
    ) -> CodeLocation | None:

        if result.symbol_name:

            symbols = (
                await self.index.find_symbol(
                    result.symbol_name
                )
            )

            matching = next(
                (
                    symbol
                    for symbol in symbols
                    if symbol.file_path
                    == result.file_path
                ),
                None,
            )

            if matching:

                return (
                    await self.context
                    .location_for_symbol(
                        matching,
                        result.score,
                    )
                )

        return (
            await self.context
            .surrounding_location(
                result.file_path,
                result.line_number,
                result.score,
            )
        )

    async def _graph_locations(
        self,
        symbol,
        *,
        direction: str,
    ) -> list[CodeLocation]:

        visited: set[
            tuple[str, int]
        ] = set()

        current = [symbol]
        locations: list[
            CodeLocation
        ] = []

        for _ in range(
            self.call_graph_depth
        ):

            next_symbols = []

            for item in current:

                key = (
                    item.file_path,
                    item.start_line,
                )

                if key in visited:
                    continue

                visited.add(key)

                location = (
                    await self.context
                    .location_for_symbol(
                        item,
                        0.82,
                    )
                )

                locations.append(
                    location
                )

                if direction == "callers":

                    children = (
                        await self.index
                        .find_callers(item)
                    )

                else:

                    children = (
                        await self.index
                        .find_callees(item)
                    )

                next_symbols.extend(
                    children
                )

            current = next_symbols

            if not current:
                break

            if (
                len(locations)
                >= self.context.max_symbols
            ):
                break

        return _unique_locations(
            locations,
            self.context.max_symbols,
        )

    async def _related_locations(
        self,
        signal: InvestigationSignal,
        primary: CodeLocation,
    ) -> list[CodeLocation]:

        results = await self.search.search(
            signal,
            limit=50,
            candidate_limit=100,
        )

        locations: list[
            CodeLocation
        ] = []

        for result in results:

            if (
                result.file_path
                == primary.file_path
                and result.line_number
                == primary.start_line
            ):
                continue

            location = (
                await self._resolve_search_result(
                    result
                )
            )

            if not location:
                continue

            if (
                location.file_path
                == primary.file_path
                and location.start_line
                == primary.start_line
            ):
                continue

            locations.append(
                location
            )

            if (
                len(locations)
                >= self.context.max_files
            ):
                break

        return _unique_locations(
            locations,
            self.context.max_symbols,
        )

    def _safe_relative_path(
        self,
        path: str,
    ) -> str | None:

        candidate = Path(path)

        if candidate.is_absolute():
            return None

        try:

            resolved = (
                self.repository.root
                / candidate
            ).resolve(
                strict=False
            )

            resolved.relative_to(
                self.repository.root
            )

        except (
            OSError,
            ValueError,
        ):

            return None

        return str(
            resolved.relative_to(
                self.repository.root
            )
        ).replace(
            "\\",
            "/",
        )

    @staticmethod
    def _result(
        signal: InvestigationSignal,
        **kwargs: Any,
    ) -> RepositoryInvestigationResult:

        return RepositoryInvestigationResult(
            exception_type=signal.exception_type,
            message=signal.message,
            operation=signal.operation,
            **kwargs,
        )

    @staticmethod
    def _explanation(
        primary: CodeLocation,
        callers: list[CodeLocation],
        callees: list[CodeLocation],
    ) -> str:

        path = (
            f"{primary.file_path}:"
            f"{primary.start_line}"
        )

        relationships = []

        if callers:
            relationships.append(
                f"{len(callers)} caller(s)"
            )

        if callees:
            relationships.append(
                f"{len(callees)} callee(s)"
            )

        suffix = ""

        if relationships:

            suffix = (
                "; found "
                + ", ".join(relationships)
            )

        return (
            "The highest-ranked repository "
            f"evidence is {path}{suffix}."
        )

    @staticmethod
    def _incident_identifiers(
        traces: list[TraceEntry],
        logs: list[LogEntry],
    ) -> list[str]:

        identifiers: list[str] = []

        for trace in traces:

            for key, value in trace.attributes.items():

                if (
                    isinstance(
                        value,
                        (
                            str,
                            int,
                            float,
                        ),
                    )
                    and key
                    not in {
                        "error",
                        "route",
                        "path",
                    }
                ):

                    identifiers.extend(
                        [
                            str(key),
                            str(value),
                        ]
                    )

        for log in logs:

            identifiers.extend(
                _identifier_tokens(
                    log.message
                )
            )

        return list(
            dict.fromkeys(
                item
                for item in identifiers
                if len(item) >= 3
            )
        )[:20]


async def investigate_repository(
    exception: ExceptionEntry,
    traces: list[TraceEntry] | None = None,
    logs: list[LogEntry] | None = None,
    repository_path: str | Path | None = None,
) -> RepositoryInvestigationResult:

    path = (
        repository_path
        or settings.repository_path
    )

    if not path:

        return RepositoryInvestigationResult(
            exception_type=exception.exception_type,
            message=exception.message,
            operation=exception.operation,
            explanation=(
                "Repository analysis unavailable "
                "because no repository path "
                "is configured."
            ),
        )

    try:

        engine = RepositoryInvestigationEngine(
            path,
            ignored_dirs=set(
                settings.repository_ignored_dirs
            ),
            max_files=settings.repository_max_files,
            max_results=(
                settings.repository_max_search_results
            ),
            call_graph_depth=(
                settings.repository_call_graph_depth
            ),
            max_context_files=(
                settings.repository_max_context_files
            ),
            max_context_symbols=(
                settings.repository_max_context_symbols
            ),
            max_lines_per_symbol=(
                settings.repository_max_lines_per_symbol
            ),
        )

        return await engine.investigate(
            exception,
            traces,
            logs,
        )

    except (
        OSError,
        RuntimeError,
        ValueError,
    ) as error:

        return RepositoryInvestigationResult(
            exception_type=exception.exception_type,
            message=exception.message,
            operation=exception.operation,
            explanation=(
                "Repository investigation "
                f"failed safely: {error}"
            ),
        )


def _unique_locations(
    locations: list[CodeLocation],
    limit: int,
) -> list[CodeLocation]:

    unique: dict[
        tuple[str, int, int],
        CodeLocation,
    ] = {}

    for location in locations:

        key = (
            location.file_path,
            location.start_line,
            location.end_line,
        )

        unique[key] = location

    return list(
        unique.values()
    )[:limit]


def _identifier_tokens(
    text: str,
) -> list[str]:

    return [
        token
        for token in (
            text
            .replace("=", " ")
            .replace(":", " ")
            .split()
        )
        if len(token) >= 3
        and (
            token.isupper()
            or "_" in token
            or token.isalnum()
        )
    ]