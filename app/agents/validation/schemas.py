from enum import Enum

from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class PredictionEvaluation(BaseModel):
    prediction: str

    expected: str

    observed: str

    matched: bool

    explanation: str

    confidence_delta: float = Field(
        ge=-1.0,
        le=1.0,
    )


class ValidationResult(BaseModel):
    hypothesis_id: str

    hypothesis: str

    status: ValidationStatus

    original_confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    updated_confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    prediction_evaluations: list[
        PredictionEvaluation
    ] = Field(
        default_factory=list
    )

    supporting_evidence: list[str] = Field(
        default_factory=list
    )

    contradicting_evidence: list[str] = Field(
        default_factory=list
    )

    reasoning: str

    recommended_next_step: str