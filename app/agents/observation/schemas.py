from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str
    service: str
    operation: str | None = None
    exception_type: str | None = None


class MetricSnapshot(BaseModel):
    timestamp: datetime
    service: str

    request_count: int
    error_count: int

    error_rate: float
    latency_p50_ms: float
    latency_p95_ms: float

    cpu_percent: float
    memory_percent: float


class TraceEntry(BaseModel):
    timestamp: datetime
    trace_id: str
    span_id: str

    service: str
    operation: str

    duration_ms: float
    status: str

    attributes: dict[str, Any] = Field(default_factory=dict)


class ExceptionEntry(BaseModel):
    timestamp: datetime
    service: str
    exception_type: str
    message: str
    operation: str | None = None


class ObservationSnapshot(BaseModel):
    timestamp: datetime
    project_id: str
    service: str

    logs: list[LogEntry]
    metrics: MetricSnapshot
    traces: list[TraceEntry]
    exceptions: list[ExceptionEntry]

    health_status: str