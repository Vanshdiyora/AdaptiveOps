from app.services.observation_service import (
    ObservationService,
)


class ObservationAgent:

    name = "observation_agent"

    def __init__(self):

        self.observation_service = (
            ObservationService()
        )

    async def run(
        self,
        project_id: str,
        service: str,
        minutes: int = 10
    ):

        print(
            f"\n[Observation Agent]"
            f" Observing service: {service}"
        )

        snapshot = await (
            self.observation_service.observe(
                project_id=project_id,
                service=service,
                minutes=minutes
            )
        )

        print(
            f"[Observation Agent]"
            f" Health: {snapshot.health_status}"
        )

        return snapshot