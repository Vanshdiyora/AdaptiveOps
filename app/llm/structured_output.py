from pydantic import BaseModel, Field

from app.core.incident_models import Correlation, TimelineEvent


class InvestigationLLMOutput(BaseModel):
	correlations: list[Correlation] = Field(default_factory=list)
	timeline: list[TimelineEvent] = Field(default_factory=list)
	affected_dependencies: list[str] = Field(default_factory=list)
	summary: str = Field(min_length=1)
	uncertainties: list[str] = Field(default_factory=list)
