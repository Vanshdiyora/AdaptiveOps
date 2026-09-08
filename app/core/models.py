from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.enums import (
    EvidenceType,
    IncidentSeverity,
    IncidentStatus,
)


class DetectionReason(BaseModel):
    rule: str
    message: str
    severity: IncidentSeverity


class DetectionResult(BaseModel):
    detected: bool
    severity: IncidentSeverity | None = None
    reasons: list[DetectionReason] = Field(default_factory=list)


class Incident(BaseModel):
    incident_id: str
    project_id: str
    service: str

    severity: IncidentSeverity
    status: IncidentStatus

    detected_at: datetime

    trigger: DetectionResult

    observation: Any | None = None


class Evidence(BaseModel):
    evidence_id: str

    type: EvidenceType

    source: str
    signal: str

    value: Any

    severity: str | None = None

    timestamp: datetime | None = None

    description: str


class Correlation(BaseModel):
    source_evidence_id: str
    target_evidence_id: str

    relationship: str

    confidence: float = Field(ge=0.0, le=1.0)


class TimelineEvent(BaseModel):
    timestamp: datetime
    event_type: str
    description: str

    evidence_ids: list[str] = Field(default_factory=list)


class InvestigationResult(BaseModel):
    incident_id: str
    service: str

    evidence: list[Evidence] = Field(default_factory=list)

    correlations: list[Correlation] = Field(default_factory=list)

    timeline: list[TimelineEvent] = Field(default_factory=list)

    affected_dependencies: list[str] = Field(default_factory=list)

    investigation_summary: str

    status: str = "COMPLETE"