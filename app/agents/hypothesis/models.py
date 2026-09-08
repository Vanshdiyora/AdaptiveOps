from pydantic import BaseModel, Field


class Hypothesis(BaseModel):
    hypothesis: str = Field(
        description="Possible root cause of the incident."
    )

    confidence: float = Field(
        description="Confidence score between 0 and 1."
    )

    supporting_evidence: list[str] = Field(
        description="Evidence supporting the hypothesis."
    )

    contradicting_evidence: list[str] = Field(
        description="Evidence contradicting the hypothesis."
    )

    validation_strategy: str = Field(
        description="Safe method for validating the hypothesis."
    )


class HypothesisResult(BaseModel):
    hypotheses: list[Hypothesis] = Field(
        description="List of competing root cause hypotheses."
    )

    primary_hypothesis: str = Field(
        description="Most likely root cause."
    )

    reasoning_summary: str = Field(
        description="Short explanation of the reasoning."
    )