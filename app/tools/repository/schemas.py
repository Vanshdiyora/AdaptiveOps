from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CodeChunk:
    """
    A searchable piece of repository source code.
    """

    chunk_id: str
    repository_id: str
    file_path: str
    language: str
    content: str
    start_line: int
    end_line: int
    chunk_index: int
    symbol: str | None = None
    chunk_type: str = "code"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def searchable_text(self) -> str:
        parts = [
            f"file: {self.file_path}",
            f"language: {self.language}",
        ]
        if self.symbol:
            parts.append(f"symbol: {self.symbol}")
        parts.append(self.content)
        return "\n".join(parts)


@dataclass(slots=True)
class SemanticCandidate:
    """A semantic search result returned from Qdrant."""

    chunk_id: str
    repository_id: str
    file_path: str
    language: str
    content: str
    score: float
    start_line: int
    end_line: int
    symbol: str | None = None
    chunk_type: str = "code"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CodeLocation:
    file_path: str
    start_line: int
    end_line: int
    symbol_name: str | None = None
    symbol_type: str | None = None
    code: str = ""
    score: float = 0.0

    def model_dump(self, *, mode: str | None = None, **kwargs: Any) -> dict[str, Any]:
        payload = {
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "symbol_name": self.symbol_name,
            "symbol_type": self.symbol_type,
            "code": self.code,
            "score": self.score,
        }
        if mode == "json":
            return payload
        return payload


@dataclass(slots=True)
class StackFrame:
    file_path: str | None = None
    line_number: int | None = None
    function_name: str | None = None
    class_name: str | None = None
    module_name: str | None = None

    def model_dump(self, *, mode: str | None = None, **kwargs: Any) -> dict[str, Any]:
        payload = {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "function_name": self.function_name,
            "class_name": self.class_name,
            "module_name": self.module_name,
        }
        if mode == "json":
            return payload
        return payload


@dataclass(slots=True)
class InvestigationSignal:
    exception_type: str
    message: str
    operation: str | None = None
    frames: list[StackFrame] = field(default_factory=list)
    identifiers: list[str] = field(default_factory=list)

    def model_dump(self, *, mode: str | None = None, **kwargs: Any) -> dict[str, Any]:
        payload = {
            "exception_type": self.exception_type,
            "message": self.message,
            "operation": self.operation,
            "frames": [frame.model_dump(mode=mode, **kwargs) for frame in self.frames],
            "identifiers": list(self.identifiers),
        }
        return payload


@dataclass(slots=True)
class RepositorySearchResult:
    file_path: str
    line_number: int
    score: float
    symbol_name: str | None = None
    content: str = ""
    matched_text: str = ""

    def model_copy(self, *, update: dict[str, Any] | None = None):
        data = {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "score": self.score,
            "symbol_name": self.symbol_name,
            "content": self.content,
            "matched_text": self.matched_text,
        }
        if update:
            data.update(update)
        return RepositorySearchResult(**data)


@dataclass(slots=True)
class RepositoryInvestigationResult:
    exception_type: str
    message: str
    operation: str | None = None
    primary_location: CodeLocation | None = None
    related_locations: list[CodeLocation] = field(default_factory=list)
    callers: list[CodeLocation] = field(default_factory=list)
    callees: list[CodeLocation] = field(default_factory=list)
    explanation: str = ""

    def model_dump(self, *, mode: str | None = None, **kwargs: Any) -> dict[str, Any]:
        payload = {
            "exception_type": self.exception_type,
            "message": self.message,
            "operation": self.operation,
            "primary_location": self.primary_location.model_dump(mode=mode, **kwargs) if self.primary_location else None,
            "related_locations": [location.model_dump(mode=mode, **kwargs) for location in self.related_locations],
            "callers": [location.model_dump(mode=mode, **kwargs) for location in self.callers],
            "callees": [location.model_dump(mode=mode, **kwargs) for location in self.callees],
            "explanation": self.explanation,
        }
        return payload


__all__ = [
    "CodeChunk",
    "SemanticCandidate",
    "CodeLocation",
    "StackFrame",
    "InvestigationSignal",
    "RepositorySearchResult",
    "RepositoryInvestigationResult",
]
