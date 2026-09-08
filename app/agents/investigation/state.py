from typing import TypedDict

from app.core.incident_models import Evidence, Incident, InvestigationResult
from app.llm.structured_output import InvestigationLLMOutput


class InvestigationState(TypedDict, total=False):
    incident: Incident
    evidence: list[Evidence]
    investigation_context: dict[str, str]
    llm_output: InvestigationLLMOutput
    investigation_result: InvestigationResult
    error: str | None