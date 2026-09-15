from typing import Any, TypedDict

from app.core.incident_models import (
    Evidence,
    Incident,
)
from app.llm.structured_output import (
    InvestigationLLMOutput,
)


class InvestigationState(TypedDict, total=False):
    incident: Incident

    evidence: list[Evidence]

    repository_path: str | None

    code_evidence: list[dict[str, Any]]

    code_findings: list[dict[str, Any]]

    code_change_suggestions: list[dict[str, Any]]

    repository_investigation: dict[str, Any] | None

    investigation_context: dict[str, str]

    llm_output: InvestigationLLMOutput

    investigation_result: Any

    error: str | None