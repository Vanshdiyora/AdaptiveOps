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

    def _now(self):
        return datetime.now(timezone.utc)

    async def get_logs(
        self,
        service: str,
        minutes: int
    ) -> list[LogEntry]:

        now = self._now()

        return [
            LogEntry(
                timestamp=now - timedelta(seconds=45),
                level="INFO",
                service=service,
                operation="CreateOrder",
                message="Order request received"
            ),

            LogEntry(
                timestamp=now - timedelta(seconds=30),
                level="WARNING",
                service=service,
                operation="CreateOrder",
                message="Redis connection pool utilization above 80%"
            ),

            LogEntry(
                timestamp=now - timedelta(seconds=15),
                level="ERROR",
                service=service,
                operation="CreateOrder",
                message="Redis connection timeout"
            ),

            LogEntry(
                timestamp=now - timedelta(seconds=10),
                level="ERROR",
                service=service,
                operation="CreateOrder",
                message="Failed to process order",
                exception_type="RedisTimeoutException"
            ),
        ]

    async def get_metrics(
        self,
        service: str,
        minutes: int
    ) -> MetricSnapshot:

        now = self._now()

        return MetricSnapshot(
            timestamp=now,
            service=service,

            request_count=1250,
            error_count=185,

            error_rate=14.8,

            latency_p50_ms=620,
            latency_p95_ms=2450,

            cpu_percent=82.5,
            memory_percent=91.3,
        )

    async def get_traces(
        self,
        service: str,
        minutes: int
    ) -> list[TraceEntry]:

        now = self._now()

        return [
            TraceEntry(
                timestamp=now - timedelta(seconds=20),
                trace_id="trace-001",
                span_id="span-001",
                service=service,
                operation="CreateOrder",
                duration_ms=2480,
                status="ERROR",
                attributes={
                    "dependency": "redis",
                    "error": "connection_timeout"
                }
            ),

            TraceEntry(
                timestamp=now - timedelta(seconds=18),
                trace_id="trace-002",
                span_id="span-002",
                service=service,
                operation="ValidateOrder",
                duration_ms=125,
                status="OK",
            ),

            TraceEntry(
                timestamp=now - timedelta(seconds=12),
                trace_id="trace-003",
                span_id="span-003",
                service=service,
                operation="CreateOrder",
                duration_ms=2700,
                status="ERROR",
                attributes={
                    "dependency": "redis",
                    "error": "connection_timeout"
                }
            ),
        ]

    async def get_exceptions(
        self,
        service: str,
        minutes: int
    ) -> list[ExceptionEntry]:

        now = self._now()

        return [
            ExceptionEntry(
                timestamp=now - timedelta(seconds=15),
                service=service,
                exception_type="RedisTimeoutException",
                message="Unable to acquire Redis connection",
                operation="CreateOrder"
            ),

            ExceptionEntry(
                timestamp=now - timedelta(seconds=8),
                service=service,
                exception_type="TimeoutError",
                message="Redis operation exceeded timeout",
                operation="CreateOrder"
            ),
        ]