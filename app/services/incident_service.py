from datetime import datetime, timezone
from uuid import uuid4

from app.core.incident_models import (
    Incident,
    IncidentStatus,
)
from app.detection.detection import DetectionEngine


class IncidentService:

    def __init__(self):

        self.detector = DetectionEngine()

    def detect(
        self,
        observation
    ) -> Incident | None:

        detection = self.detector.detect(
            observation
        )

        if not detection.detected:
            return None

        incident = Incident(
            incident_id=(
                f"INC-{uuid4().hex[:8].upper()}"
            ),

            project_id=observation.project_id,

            service=observation.service,

            severity=detection.severity,

            status=IncidentStatus.DETECTED,

            detected_at=datetime.now(
                timezone.utc
            ),

            trigger=detection,

            observation=observation,
        )

        return incident