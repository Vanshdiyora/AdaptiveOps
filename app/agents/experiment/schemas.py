from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExperimentType(str, Enum):
    SERVICE_HEALTH = "service_health"
    DEPENDENCY_LATENCY = "dependency_latency"
    CONNECTION_POOL = "connection_pool"
    ERROR_RATE = "error_rate"
    RECENT_DEPLOYMENT = "recent_deployment"
    VERSION_COMPARISON = "version_comparison"
    METRIC_COMPARISON = "metric_comparison"
    LOG_PATTERN = "log_pattern"


class ExperimentRequest(BaseModel):
    experiment_id: str
    hypothesis_id: str

    experiment_type: ExperimentType

    target: str

    parameters: dict[str, Any] = Field(
        default_factory=dict
    )

    expected_observations: list[str] = Field(
        default_factory=list
    )

    rationale: str

    risk_level: str = "READ_ONLY"


class ExperimentPlan(BaseModel):
    experiments: list[ExperimentRequest] = Field(
        min_length=1,
        max_length=5
    )

class ExperimentObservation(BaseModel):
    name: str
    value: Any
    unit: str | None = None
    source: str = "experiment_tool"
    timestamp: str | None = None


class ExperimentResult(BaseModel):
    experiment_id: str

    hypothesis_id: str

    experiment_type: ExperimentType

    target: str

    success: bool

    observations: list[ExperimentObservation] = Field(
        default_factory=list
    )

    raw_result: dict[str, Any] = Field(
        default_factory=dict
    )

    error: str | None = None

    execution_time_ms: float | None = None