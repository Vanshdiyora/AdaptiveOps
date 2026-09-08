from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IncidentSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    DETECTED = "DETECTED"
    INVESTIGATING = "INVESTIGATING"
    HYPOTHESIS_GENERATED = "HYPOTHESIS_GENERATED"
    VALIDATING = "VALIDATING"
    ROOT_CAUSE_IDENTIFIED = "ROOT_CAUSE_IDENTIFIED"
    ACTION_PLANNED = "ACTION_PLANNED"
    POLICY_CHECK = "POLICY_CHECK"
    REMEDIATING = "REMEDIATING"
    VERIFYING = "VERIFYING"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"


class DetectionReason(BaseModel):
    rule: str
    message: str
    severity: IncidentSeverity


class DetectionResult(BaseModel):
    detected: bool
    severity: IncidentSeverity | None = None

    reasons: list[DetectionReason] = Field(
        default_factory=list
    )


class Incident(BaseModel):
    incident_id: str

    project_id: str
    service: str

    severity: IncidentSeverity
    status: IncidentStatus

    detected_at: datetime

    trigger: DetectionResult

    observation: Any


class EvidenceType(str, Enum):
    METRIC = "METRIC"
    LOG = "LOG"
    TRACE = "TRACE"
    EXCEPTION = "EXCEPTION"
    DEPENDENCY = "DEPENDENCY"


class Evidence(BaseModel):
    evidence_id: str

    type: EvidenceType

    source: str
    signal: str

    value: Any

    severity: str | None = None

    description: str


class Correlation(BaseModel):
    source_evidence_id: str
    target_evidence_id: str

    relationship: str

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )


class TimelineEvent(BaseModel):
    event_type: str
    description: str

    evidence_ids: list[str] = Field(
        default_factory=list
    )


class InvestigationResult(BaseModel):
    incident_id: str

    project_id: str
    service: str

    evidence: list[Evidence] = Field(
        default_factory=list
    )

    correlations: list[Correlation] = Field(
        default_factory=list
    )

    timeline: list[TimelineEvent] = Field(
        default_factory=list
    )

    affected_dependencies: list[str] = Field(
        default_factory=list
    )

    summary: str

    uncertainties: list[str] = Field(
        default_factory=list
    )

    status: str = "COMPLETE"