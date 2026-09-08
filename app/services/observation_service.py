from datetime import datetime, timezone

from app.agents.observation.schemas import (
    ObservationSnapshot,
)

from app.tools.observability.application_insights import (
    create_observability_provider,
)


class ObservationService:

    def __init__(self):

        self.provider = (
            create_observability_provider()
        )

    async def observe(
        self,
        project_id: str,
        service: str,
        minutes: int
    ) -> ObservationSnapshot:

        logs = await self.provider.get_logs(
            service,
            minutes
        )

        metrics = await self.provider.get_metrics(
            service,
            minutes
        )

        traces = await self.provider.get_traces(
            service,
            minutes
        )

        exceptions = await self.provider.get_exceptions(
            service,
            minutes
        )

        health_status = self.calculate_health(
            metrics,
            exceptions
        )

        return ObservationSnapshot(
            timestamp=datetime.now(timezone.utc),

            project_id=project_id,

            service=service,

            logs=logs,

            metrics=metrics,

            traces=traces,

            exceptions=exceptions,

            health_status=health_status
        )

    def calculate_health(
        self,
        metrics,
        exceptions
    ):

        if metrics.error_rate >= 10:
            return "CRITICAL"

        if metrics.error_rate >= 5:
            return "DEGRADED"

        if len(exceptions) > 0:
            return "DEGRADED"

        return "HEALTHY"