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
                timestamp=now - timedelta(seconds=60),
                level="INFO",
                service="frontend",
                operation="POST /api/workflow/last",
                message=(
                    "Workflow run request received from frontend"
                ),
            ),

            LogEntry(
                timestamp=now - timedelta(seconds=50),
                level="INFO",
                service="frontend",
                operation="POST /api/workflow/last",
                message=(
                    "Request URL: "
                    "http://localhost:5173/api/workflow/last"
                ),
            ),

            LogEntry(
                timestamp=now - timedelta(seconds=40),
                level="ERROR",
                service="frontend",
                operation="POST /api/workflow/last",
                message=(
                    '127.0.0.1:50810 - '
                    '"POST /api/workflow/last HTTP/1.1" '
                    "404 Not Found"
                ),
                exception_type="HTTPNotFound",
            ),

            LogEntry(
                timestamp=now - timedelta(seconds=30),
                level="ERROR",
                service="frontend",
                operation="POST /api/workflow/last",
                message=(
                    "Workflow API endpoint "
                    "/api/workflow/last returned 404 Not Found"
                ),
                exception_type="HTTPNotFound",
            ),

            LogEntry(
                timestamp=now - timedelta(seconds=20),
                level="ERROR",
                service="frontend",
                operation="POST /api/workflow/last",
                message=(
                    "POST request failed because "
                    "/api/workflow/last is not registered "
                    "on the application running at localhost:5173"
                ),
                exception_type="HTTPNotFound",
            ),

            LogEntry(
                timestamp=now - timedelta(seconds=10),
                level="INFO",
                service="frontend",
                operation="POST /api/workflow/last",
                message=(
                    "Workflow request completed with HTTP status 404"
                ),
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

            # Request reaches the application and gets
            # an HTTP response, so latency is non-zero.
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
                trace_id="trace-workflow-001",
                span_id="span-frontend-001",
                service="frontend",
                operation="POST /api/workflow/last",
                duration_ms=16,
                status="ERROR",
                attributes={
                    "http_method": "POST",
                    "http_url": (
                        "http://localhost:5173/api/workflow/last"
                    ),
                    "http_status": 404,
                    "error": "Not Found",
                    "route": "/api/workflow/last",
                },
            ),

            TraceEntry(
                timestamp=now - timedelta(seconds=30),
                trace_id="trace-workflow-002",
                span_id="span-frontend-002",
                service="frontend",
                operation="POST /api/workflow/last",
                duration_ms=21,
                status="ERROR",
                attributes={
                    "http_method": "POST",
                    "target": "localhost:5173",
                    "path": "/api/workflow/last",
                    "status_code": 404,
                    "error_type": "HTTPNotFound",
                },
            ),

            TraceEntry(
                timestamp=now - timedelta(seconds=15),
                trace_id="trace-workflow-003",
                span_id="span-frontend-003",
                service="frontend",
                operation="POST /api/workflow/last",
                duration_ms=39,
                status="ERROR",
                attributes={
                    "http_method": "POST",
                    "path": "/api/workflow/last",
                    "response_status": 404,
                    "reason": (
                        "No matching API route was found"
                    ),
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
                timestamp=now - timedelta(seconds=40),
                service="frontend",
                exception_type="HTTPNotFound",
                message=(
                    "POST /api/workflow/last returned "
                    "404 Not Found"
                ),
                operation="POST /api/workflow/last",
            ),

            ExceptionEntry(
                timestamp=now - timedelta(seconds=30),
                service="frontend",
                exception_type="HTTPNotFound",
                message=(
                    "Workflow API endpoint "
                    "/api/workflow/last was not found "
                    "on localhost:5173"
                ),
                operation="POST /api/workflow/last",
            ),

            ExceptionEntry(
                timestamp=now - timedelta(seconds=15),
                service="frontend",
                exception_type="HTTPNotFound",
                message=(
                    "No route matched POST /api/workflow/last"
                ),
                operation="POST /api/workflow/last",
            ),
        ]