from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.core.incident_models import Correlation, TimelineEvent


class InvestigationLLMOutput(BaseModel):
    correlations: list[Correlation] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    affected_dependencies: list[str] = Field(default_factory=list)

    summary: str = Field(min_length=1)

    uncertainties: list[str] = Field(default_factory=list)

    code_evidence: list[dict[str, Any]] = Field(
        default_factory=list
    )

    code_findings: list[dict[str, Any]] = Field(
        default_factory=list
    )

    code_change_suggestions: list[dict[str, Any]] = Field(
        default_factory=list
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_llm_output(cls, value: Any) -> Any:
        """
        Normalize common LLM output variations into the canonical
        InvestigationLLMOutput schema.

        The LLM sometimes returns:
            correlations:
                {"evidence_ids": ["A", "B"], ...}

        instead of:
                {"source_evidence_id": "A",
                 "target_evidence_id": "B", ...}

        It may also return:
            timeline:
                {"event": "...", "description": "..."}

        instead of:
                {"event_type": "...", "description": "..."}

        And:
            affected_dependencies:
                {"dependency": "...", "confidence": 0.9}

        instead of:
                "..."
        """

        if not isinstance(value, dict):
            return value

        value = dict(value)

        # ---------------------------------------------------------
        # Normalize correlations
        # ---------------------------------------------------------
        normalized_correlations = []

        for correlation in value.get("correlations", []) or []:
            if not isinstance(correlation, dict):
                continue

            correlation = dict(correlation)

            evidence_ids = correlation.get("evidence_ids")

            if evidence_ids:
                if (
                    "source_evidence_id" not in correlation
                    and len(evidence_ids) >= 1
                ):
                    correlation["source_evidence_id"] = (
                        evidence_ids[0]
                    )

                if (
                    "target_evidence_id" not in correlation
                    and len(evidence_ids) >= 2
                ):
                    correlation["target_evidence_id"] = (
                        evidence_ids[1]
                    )

                correlation.pop("evidence_ids", None)

            normalized_correlations.append(correlation)

        value["correlations"] = normalized_correlations

        # ---------------------------------------------------------
        # Normalize timeline
        # ---------------------------------------------------------
        normalized_timeline = []

        for event in value.get("timeline", []) or []:
            if not isinstance(event, dict):
                continue

            event = dict(event)

            if (
                "event_type" not in event
                and "event" in event
            ):
                event["event_type"] = event.pop("event")

            if "evidence_ids" not in event:
                event["evidence_ids"] = []

            normalized_timeline.append(event)

        value["timeline"] = normalized_timeline

        # ---------------------------------------------------------
        # Normalize affected dependencies
        # ---------------------------------------------------------
        normalized_dependencies = []

        for dependency in (
            value.get("affected_dependencies", []) or []
        ):
            if isinstance(dependency, str):
                normalized_dependencies.append(dependency)

            elif isinstance(dependency, dict):
                dependency_name = dependency.get(
                    "dependency"
                )

                if dependency_name:
                    normalized_dependencies.append(
                        str(dependency_name)
                    )

        value["affected_dependencies"] = (
            normalized_dependencies
        )

        # ---------------------------------------------------------
        # Normalize optional code sections
        # ---------------------------------------------------------
        value["code_evidence"] = (
            value.get("code_evidence") or []
        )

        value["code_findings"] = (
            value.get("code_findings") or []
        )

        value["code_change_suggestions"] = (
            value.get("code_change_suggestions") or []
        )

        value["uncertainties"] = (
            value.get("uncertainties") or []
        )

        return value