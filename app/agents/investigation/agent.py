import json
import logging

from langchain_core.runnables import Runnable

from app.core.incident_models import Evidence, EvidenceType, Incident
from app.llm.structured_output import InvestigationLLMOutput


logger = logging.getLogger(__name__)


class InvestigationAgent:
    def __init__(self, reasoning_chain: Runnable):
        self.reasoning_chain = reasoning_chain

    def collect_evidence(self, incident: Incident) -> list[Evidence]:
        logger.info("[Investigation] Collecting evidence")
        observation = incident.observation
        metrics = observation.metrics

        evidence = [
            Evidence(
                evidence_id="METRIC-001",
                type=EvidenceType.METRIC,
                source="observation",
                signal="request_count",
                value=metrics.request_count,
                description=f"{metrics.request_count} requests were observed.",
            ),
            Evidence(
                evidence_id="METRIC-002",
                type=EvidenceType.METRIC,
                source="observation",
                signal="error_count",
                value=metrics.error_count,
                description=f"{metrics.error_count} failed requests were observed.",
            ),
            Evidence(
                evidence_id="METRIC-003",
                type=EvidenceType.METRIC,
                source="observation",
                signal="error_rate",
                value=metrics.error_rate,
                description=f"Error rate is {metrics.error_rate}%.",
            ),
            Evidence(
                evidence_id="METRIC-004",
                type=EvidenceType.METRIC,
                source="observation",
                signal="latency_p50_ms",
                value=metrics.latency_p50_ms,
                description=f"P50 latency is {metrics.latency_p50_ms}ms.",
            ),
            Evidence(
                evidence_id="METRIC-005",
                type=EvidenceType.METRIC,
                source="observation",
                signal="latency_p95_ms",
                value=metrics.latency_p95_ms,
                description=f"P95 latency is {metrics.latency_p95_ms}ms.",
            ),
        ]

        for index, log in enumerate(observation.logs, start=1):
            evidence.append(
                Evidence(
                    evidence_id=f"LOG-{index:03d}",
                    type=EvidenceType.LOG,
                    source="application_logs",
                    signal=log.level,
                    value=log.message,
                    severity=log.level,
                    description=log.message,
                )
            )

        for index, trace in enumerate(observation.traces, start=1):
            evidence.append(
                Evidence(
                    evidence_id=f"TRACE-{index:03d}",
                    type=EvidenceType.TRACE,
                    source="distributed_tracing",
                    signal=trace.operation,
                    value={
                        "duration_ms": trace.duration_ms,
                        "status": trace.status,
                    },
                    severity=trace.status,
                    description=(
                        f"{trace.operation} took {trace.duration_ms}ms "
                        f"and returned {trace.status}."
                    ),
                )
            )

        for index, exception in enumerate(observation.exceptions, start=1):
            evidence.append(
                Evidence(
                    evidence_id=f"EXCEPTION-{index:03d}",
                    type=EvidenceType.EXCEPTION,
                    source="exception_tracking",
                    signal=exception.exception_type,
                    value=exception.message,
                    severity="ERROR",
                    description=(
                        f"{exception.exception_type}: {exception.message}"
                    ),
                )
            )

        return evidence

    @staticmethod
    def prepare_context(
        incident: Incident,
        evidence: list[Evidence],
    ) -> dict[str, str]:
        incident_context = {
            "incident_id": incident.incident_id,
            "project_id": incident.project_id,
            "service": incident.service,
            "severity": incident.severity.value,
            "status": incident.status.value,
            "detection_reasons": [
                reason.model_dump(mode="json")
                for reason in incident.trigger.reasons
            ],
        }
        evidence_context = [item.model_dump(mode="json") for item in evidence]
        return {
            "incident_context": json.dumps(incident_context, indent=2),
            "evidence_context": json.dumps(evidence_context, indent=2),
        }

    async def investigate(
        self,
        context: dict[str, str],
    ) -> InvestigationLLMOutput:

        logger.info("[LLM] Investigation reasoning started")

        output = await self.reasoning_chain.ainvoke(context)

        result = InvestigationLLMOutput.model_validate(output)

        logger.info("[LLM] Investigation reasoning completed")

        return result