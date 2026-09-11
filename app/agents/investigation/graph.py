import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.investigation.agent import InvestigationAgent
from app.agents.investigation.state import InvestigationState
from app.config.settings import settings
from app.core.incident_models import (
    IncidentStatus,
    InvestigationResult,
)


logger = logging.getLogger(__name__)


def build_investigation_graph(
    agent: InvestigationAgent,
) -> CompiledStateGraph:

    def load_incident(
        state: InvestigationState,
    ) -> dict:

        incident = state["incident"]
        incident.status = IncidentStatus.INVESTIGATING

        return {
            "incident": incident,
            "error": None,
        }

    def collect_repository_evidence(
        state: InvestigationState,
    ) -> dict:

        repository_payload = (
            agent.investigate_repository(
                state["incident"]
            )
        )

        return {
            "repository_path": settings.repository_path,

            "code_evidence": repository_payload.get(
                "code_evidence",
                [],
            ),

            "code_findings": repository_payload.get(
                "code_findings",
                [],
            ),

            "code_change_suggestions": (
                repository_payload.get(
                    "code_change_suggestions",
                    [],
                )
            ),
        }

    def prepare_investigation_context(
        state: InvestigationState,
    ) -> dict:

        repository_context = {
            "repository_path": state.get(
                "repository_path"
            ),

            "code_evidence": state.get(
                "code_evidence",
                [],
            ),

            "code_findings": state.get(
                "code_findings",
                [],
            ),

            "code_change_suggestions": (
                state.get(
                    "code_change_suggestions",
                    [],
                )
            ),
        }

        return {
            "investigation_context": (
                agent.prepare_context(
                    state["incident"],
                    state.get("evidence", []),
                    state["incident"].observation,
                    repository_context,
                )
            )
        }

    async def llm_investigate(
        state: InvestigationState,
    ) -> dict:

        try:
            output = await agent.investigate(
                state["investigation_context"]
            )

            return {
                "llm_output": output,
                "error": None,
            }

        except Exception as error:
            logger.exception(
                "[LLM] Investigation reasoning failed"
            )

            return {
                "error": (
                    f"LLM investigation failed: {error}"
                )
            }

    def validate_investigation(
        state: InvestigationState,
    ) -> dict:

        try:
            output = state["llm_output"]

            evidence = state.get("evidence", [])
            evidence_ids = {
                item.evidence_id
                for item in evidence
            }

            referenced_ids = {
                evidence_id
                for correlation in output.correlations
                for evidence_id in (
                    correlation.source_evidence_id,
                    correlation.target_evidence_id,
                )
            }

            referenced_ids.update(
                evidence_id
                for event in output.timeline
                for evidence_id in event.evidence_ids
            )

            unknown_ids = referenced_ids - evidence_ids

            if evidence and unknown_ids:
                raise ValueError(
                    "LLM referenced unknown evidence IDs: "
                    + ", ".join(
                        sorted(unknown_ids)
                    )
                )

            incident = state["incident"]

            result = InvestigationResult(
                incident_id=incident.incident_id,
                project_id=incident.project_id,
                service=incident.service,

                evidence=evidence,

                correlations=output.correlations,

                timeline=output.timeline,

                affected_dependencies=(
                    output.affected_dependencies
                ),

                summary=output.summary,

                uncertainties=output.uncertainties,

                repository_path=state.get(
                    "repository_path"
                ),

                code_evidence=(
                    state.get(
                        "code_evidence",
                        [],
                    )
                    or output.code_evidence
                ),

                code_findings=(
                    state.get(
                        "code_findings",
                        [],
                    )
                    or output.code_findings
                ),

                code_change_suggestions=(
                    state.get(
                        "code_change_suggestions",
                        [],
                    )
                    or output.code_change_suggestions
                ),
            )

            return {
                "investigation_result": result,
                "error": None,
            }

        except Exception as error:
            logger.exception(
                "[Investigation] Structured output validation failed"
            )

            return {
                "error": (
                    "Investigation validation failed: "
                    f"{error}"
                )
            }

    def investigation_failed(
        state: InvestigationState,
    ) -> dict:

        logger.error(
            "[LangGraph] Investigation workflow failed: %s",
            state["error"],
        )

        return {}

    def route_after_llm(
        state: InvestigationState,
    ) -> str:

        return (
            "failed"
            if state.get("error")
            else "validate"
        )

    def route_after_validation(
        state: InvestigationState,
    ) -> str:

        return (
            "failed"
            if state.get("error")
            else "complete"
        )

    graph = StateGraph(InvestigationState)

    graph.add_node(
        "load_incident",
        load_incident,
    )

    graph.add_node(
        "collect_repository_evidence",
        collect_repository_evidence,
    )

    graph.add_node(
        "prepare_investigation_context",
        prepare_investigation_context,
    )

    graph.add_node(
        "llm_investigate",
        llm_investigate,
    )

    graph.add_node(
        "validate_investigation",
        validate_investigation,
    )

    graph.add_node(
        "investigation_failed",
        investigation_failed,
    )

    graph.add_edge(
        START,
        "load_incident",
    )

    graph.add_edge(
        "load_incident",
        "collect_repository_evidence",
    )

    graph.add_edge(
        "collect_repository_evidence",
        "prepare_investigation_context",
    )

    graph.add_edge(
        "prepare_investigation_context",
        "llm_investigate",
    )

    graph.add_conditional_edges(
        "llm_investigate",
        route_after_llm,
        {
            "validate": "validate_investigation",
            "failed": "investigation_failed",
        },
    )

    graph.add_conditional_edges(
        "validate_investigation",
        route_after_validation,
        {
            "complete": END,
            "failed": "investigation_failed",
        },
    )

    graph.add_edge(
        "investigation_failed",
        END,
    )

    return graph.compile()