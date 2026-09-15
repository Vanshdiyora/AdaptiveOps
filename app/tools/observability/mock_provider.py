from datetime import datetime, timedelta, timezone

from app.agents.observation.schemas import (
    LogEntry,
    MetricSnapshot,
    TraceEntry,
    ExceptionEntry,
)

from app.tools.observability.provider import (
    ObservabilityProvider,
)


class MockApplicationInsightsProvider(
    ObservabilityProvider
):

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    async def get_logs(
        self,
        service: str,
        minutes: int,
    ) -> list[LogEntry]:

        now = self._now()

        return [
            LogEntry(
                timestamp=now - timedelta(seconds=50),
                level="INFO",
                service="frontend",
                operation="POST /api/workflow/run",
                message=(
                    "Workflow run request initiated "
                    "from frontend"
                ),
            ),

            LogEntry(
                timestamp=now - timedelta(seconds=40),
                level="INFO",
                service="frontend",
                operation="POST /api/workflow/run",
                message=(
                    "POST request sent to "
                    "http://localhost:5173/api/workflow/run"
                ),
            ),

            LogEntry(
                timestamp=now - timedelta(seconds=30),
                level="INFO",
                service="backend",
                operation="POST /api/workflow/run",
                message=(
                    "Workflow run request received by backend"
                ),
            ),

            LogEntry(
                timestamp=now - timedelta(seconds=20),
                level="ERROR",
                service="backend",
                operation="POST /api/workflow/run",
                message=(
                    "Workflow execution failed because "
                    "the provided ticker format is invalid"
                ),
                exception_type="InvalidTickerFormat",
            ),

            LogEntry(
                timestamp=now - timedelta(seconds=15),
                level="ERROR",
                service="backend",
                operation="POST /api/workflow/run",
                message=(
                    'Request rejected with HTTP 400: '
                    '"Invalid ticker format."'
                ),
                exception_type="HTTPBadRequest",
            ),

            LogEntry(
                timestamp=now - timedelta(seconds=10),
                level="ERROR",
                service="backend",
                operation="POST /api/workflow/run",
                message=(
                    "Ticker validation failed before "
                    "workflow execution could start"
                ),
                exception_type="InvalidTickerFormat",
            ),

            LogEntry(
                timestamp=now - timedelta(seconds=5),
                level="ERROR",
                service="frontend",
                operation="POST /api/workflow/run",
                message=(
                    "Workflow run request completed "
                    "with HTTP status 400"
                ),
                exception_type="HTTPBadRequest",
            ),
        ]

    async def get_metrics(
        self,
        service: str,
        minutes: int,
    ) -> MetricSnapshot:

        now = self._now()

        return MetricSnapshot(
            timestamp=now,
            service=service,
            request_count=120,
            error_count=10,
            error_rate=8.33,
            latency_p50_ms=18.0,
            latency_p95_ms=42.0,
            cpu_percent=12.5,
            memory_percent=34.0,
        )

    async def get_traces(
        self,
        service: str,
        minutes: int,
    ) -> list[TraceEntry]:

        now = self._now()

        return [
            TraceEntry(
                timestamp=now - timedelta(seconds=45),
                trace_id="trace-workflow-run-001",
                span_id="span-workflow-run-001",
                service="backend",
                operation="POST /api/workflow/run",
                duration_ms=16,
                status="ERROR",
                attributes={
                    "http_method": "POST",
                    "http_url": (
                        "http://localhost:8000/api/workflow/run"
                    ),
                    "http_status": 400,
                    "error": "Invalid ticker format.",
                    "route": "/api/workflow/run",
                    "ticker": "INVALID",
                },
            ),

            TraceEntry(
                timestamp=now - timedelta(seconds=30),
                trace_id="trace-workflow-run-002",
                span_id="span-workflow-run-002",
                service="backend",
                operation="POST /api/workflow/run",
                duration_ms=21,
                status="ERROR",
                attributes={
                    "http_method": "POST",
                    "target": "localhost:8000",
                    "path": "/api/workflow/run",
                    "status_code": 400,
                    "error_type": "InvalidTickerFormat",
                    "error": "Invalid ticker format.",
                    "ticker": "INVALID",
                },
            ),

            TraceEntry(
                timestamp=now - timedelta(seconds=15),
                trace_id="trace-workflow-run-003",
                span_id="span-workflow-run-003",
                service="backend",
                operation="POST /api/workflow/run",
                duration_ms=39,
                status="ERROR",
                attributes={
                    "http_method": "POST",
                    "path": "/api/workflow/run",
                    "response_status": 400,
                    "reason": (
                        "Ticker validation failed before "
                        "workflow execution could start"
                    ),
                    "error": "Invalid ticker format.",
                    "ticker": "INVALID",
                },
            ),
        ]

    async def get_exceptions(
        self,
        service: str,
        minutes: int,
    ) -> list[ExceptionEntry]:

        now = self._now()

        return [
            ExceptionEntry(
                timestamp=now - timedelta(seconds=20),
                service="backend",
                exception_type="InvalidTickerFormat",
                message=(
                    "Workflow execution failed because "
                    "the provided ticker format is invalid"
                ),
                operation="POST /api/workflow/run",
                trace_id="trace-workflow-run-001",
            ),

            ExceptionEntry(
                timestamp=now - timedelta(seconds=15),
                service="backend",
                exception_type="HTTPBadRequest",
                message=(
                    'POST /api/workflow/run returned '
                    '400 Bad Request: '
                    '"Invalid ticker format."'
                ),
                operation="POST /api/workflow/run",
            ),

            ExceptionEntry(
                timestamp=now - timedelta(seconds=10),
                service="backend",
                exception_type="InvalidTickerFormat",
                message=(
                    "Ticker validation failed before "
                    "workflow execution could start"
                ),
                operation="POST /api/workflow/run",
            ),

            ExceptionEntry(
                timestamp=now - timedelta(seconds=5),
                service="frontend",
                exception_type="HTTPBadRequest",
                message=(
                    "Frontend received HTTP 400 from "
                    "/api/workflow/run"
                ),
                operation="POST /api/workflow/run",
            ),
        ]
