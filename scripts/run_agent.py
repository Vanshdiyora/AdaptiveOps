import argparse
import asyncio
import json
import logging

from app.agents.observation.agent import ObservationAgent
from app.core.exceptions import (
    LLMConfigurationError,
    InvestigationWorkflowError,
)
from app.services.incident_service import IncidentService
from app.services.investigation_service import InvestigationService


# ============================================================
# AdaptiveOps POC Configuration
# ============================================================

PROJECT_ID = "Investment Research Agent"
SERVICE_NAME = "investment-research-agent"
OBSERVATION_MINUTES = 10

# Repository that was indexed into Qdrant.
REPOSITORY_ID = "f408137831792f38"

# Original repository path.
REPOSITORY_PATH = (
    r"C:\Work\AZDES\POC\Testing Repo"
    r"\Investment Research Agent"
    r"\Investment-Research-Agent-main"
)


# ============================================================
# CLI
# ============================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run AdaptiveOps agent workflows."
    )

    parser.add_argument(
        "command",
        nargs="?",
        default="investigation",
        choices=[
            "observation",
            "investigation",
        ],
        help=(
            "Workflow to execute. "
            "Default: investigation."
        ),
    )

    return parser


# ============================================================
# Observation Output
# ============================================================

def print_observation(observation) -> None:
    print("\n" + "=" * 60)
    print("ADAPTIVEOPS OBSERVATION")
    print("=" * 60)

    print(f"Project: {observation.project_id}")
    print(f"Service: {observation.service}")
    print(f"Health: {observation.health_status}")

    print("\n--- Metrics ---")

    print(
        f"Requests: "
        f"{observation.metrics.request_count}"
    )

    print(
        f"Errors: "
        f"{observation.metrics.error_count}"
    )

    print(
        f"Error Rate: "
        f"{observation.metrics.error_rate}%"
    )

    print(
        f"P50 Latency: "
        f"{observation.metrics.latency_p50_ms} ms"
    )

    print(
        f"P95 Latency: "
        f"{observation.metrics.latency_p95_ms} ms"
    )

    print("\n--- Logs ---")

    if observation.logs:
        for log in observation.logs:
            print(
                f"[{log.level}] "
                f"{log.message}"
            )
    else:
        print("- No logs")

    print("\n--- Traces ---")

    if observation.traces:
        for trace in observation.traces:
            print(
                f"{trace.operation} "
                f"{trace.duration_ms}ms "
                f"{trace.status}"
            )
    else:
        print("- No traces")

    print("\n--- Exceptions ---")

    if observation.exceptions:
        for exception in observation.exceptions:
            print(
                f"{exception.exception_type}: "
                f"{exception.message}"
            )
    else:
        print("- No exceptions")


# ============================================================
# Incident Detection Output
# ============================================================

def print_detection(incident) -> None:
    print("\n" + "=" * 60)
    print("ADAPTIVEOPS DETECTION")
    print("=" * 60)

    print(
        f"Incident ID: "
        f"{incident.incident_id}"
    )

    print(
        f"Severity: "
        f"{incident.severity.value}"
    )

    print(
        f"Status: "
        f"{incident.status.value}"
    )

    print("\n--- Detection Reasons ---")

    if incident.trigger.reasons:
        for reason in incident.trigger.reasons:
            print(
                f"[{reason.severity.value}] "
                f"{reason.message}"
            )
    else:
        print("- No detection reasons")


# ============================================================
# Runtime Evidence Extraction
# ============================================================

def _top_runtime_clues(
    observation,
    limit: int = 6,
):
    """
    Extract the most useful runtime signals from the
    observation.

    These clues are later used by InvestigationService
    to build the repository search query.
    """

    items = []

    # --------------------------------------------------------
    # Detection reasons
    # --------------------------------------------------------

    trigger = getattr(
        observation,
        "trigger",
        None,
    )

    if trigger:
        reasons = getattr(
            trigger,
            "reasons",
            [],
        )

        for reason in reasons:
            message = getattr(
                reason,
                "message",
                None,
            )

            if message:
                items.append(
                    {
                        "source": "detection",
                        "text": message,
                    }
                )

    # --------------------------------------------------------
    # Exceptions
    # --------------------------------------------------------

    for exception in (
        getattr(
            observation,
            "exceptions",
            [],
        )
        or []
    ):
        exception_type = getattr(
            exception,
            "exception_type",
            None,
        )

        message = getattr(
            exception,
            "message",
            None,
        )

        if exception_type and message:
            text = (
                f"{exception_type}: "
                f"{message}"
            )
        else:
            text = (
                message
                or str(exception)
            )

        if text:
            items.append(
                {
                    "source": "exception",
                    "text": text,
                }
            )

    # --------------------------------------------------------
    # Logs
    # --------------------------------------------------------

    for log in (
        getattr(
            observation,
            "logs",
            [],
        )
        or []
    ):
        level = getattr(
            log,
            "level",
            None,
        )

        message = getattr(
            log,
            "message",
            None,
        )

        if message:
            if level:
                text = (
                    f"[{level}] "
                    f"{message}"
                )
            else:
                text = message

            items.append(
                {
                    "source": "log",
                    "text": text,
                }
            )

    # --------------------------------------------------------
    # Traces
    # --------------------------------------------------------

    for trace in (
        getattr(
            observation,
            "traces",
            [],
        )
        or []
    ):
        operation = getattr(
            trace,
            "operation",
            None,
        )

        status = getattr(
            trace,
            "status",
            None,
        )

        duration = getattr(
            trace,
            "duration_ms",
            None,
        )

        if operation or status:
            text = (
                f"Operation: "
                f"{operation or 'unknown'}; "
                f"Status: "
                f"{status or 'unknown'}"
            )

            if duration is not None:
                text += (
                    f"; Duration: "
                    f"{duration}ms"
                )

            items.append(
                {
                    "source": "trace",
                    "text": text,
                }
            )

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    seen = set()
    unique = []

    for item in items:

        text = item["text"].strip()

        key = text.lower()

        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)
        unique.append(
            {
                "source": item["source"],
                "text": text,
            }
        )

        if len(unique) >= limit:
            break

    return unique


# ============================================================
# Investigation Input
# ============================================================

def build_investigation_context(
    incident,
    observation,
):
    """
    Build the structured runtime context that is passed
    into the investigation workflow.

    InvestigationService should use this information to:

        1. Understand the incident.
        2. Build a semantic repository search query.
        3. Search Qdrant.
        4. Send repository context to the LLM.
    """

    runtime_clues = _top_runtime_clues(
        observation,
        limit=6,
    )

    context = {
        "incident_id": incident.incident_id,
        "project_id": incident.project_id,
        "service": incident.service,
        "severity": incident.severity.value,
        "status": incident.status.value,
        "repository_id": REPOSITORY_ID,
        "repository_path": REPOSITORY_PATH,
        "detection_reasons": [
            reason.message
            for reason in incident.trigger.reasons
        ],
        "runtime_observations": runtime_clues,
    }

    return context


def print_investigation_context(
    incident,
    observation,
) -> None:

    payload = build_investigation_context(
        incident,
        observation,
    )

    print("\n" + "=" * 60)
    print("ADAPTIVEOPS INVESTIGATION INPUT")
    print("=" * 60)

    print(
        json.dumps(
            payload,
            indent=2,
            default=str,
        )
    )


# ============================================================
# Repository Analysis Output
# ============================================================

def print_repository_analysis(
    investigation,
) -> None:

    print("\n--- Repository Code Findings ---")

    repository_path = (
        getattr(
            investigation,
            "repository_path",
            None,
        )
        or REPOSITORY_PATH
    )

    print(
        f"Repository: "
        f"{repository_path}"
    )

    code_findings = getattr(
        investigation,
        "code_findings",
        None,
    )

    if code_findings:

        for finding in code_findings:

            print(
                f"\nFile: "
                f"{finding.get('file', 'Unknown')}"
            )

            print(
                f"Line: "
                f"{finding.get('line', 'Unknown')}"
            )

            print(
                f"Symbol: "
                f"{finding.get('symbol', 'Unknown')}"
            )

            print(
                f"Issue: "
                f"{finding.get('issue', 'Unknown')}"
            )

            print(
                f"Evidence: "
                f"{finding.get('evidence', 'Unknown')}"
            )

            confidence = finding.get(
                "confidence",
                0,
            )

            print(
                f"Confidence: "
                f"{confidence:.2f}"
            )

    else:
        print(
            "- No matching repository "
            "code was found"
        )

    # --------------------------------------------------------
    # Code Changes
    # --------------------------------------------------------

    print("\n--- Required Code Changes ---")

    suggestions = getattr(
        investigation,
        "code_change_suggestions",
        None,
    )

    if suggestions:

        for suggestion in suggestions:

            print(
                f"\nFile: "
                f"{suggestion.get('file', 'Unknown')}"
            )

            print(
                f"Line: "
                f"{suggestion.get('line', 'Unknown')}"
            )

            print(
                f"Symbol: "
                f"{suggestion.get('symbol', 'Unknown')}"
            )

            print(
                f"Problem: "
                f"{suggestion.get('problem', 'Unknown')}"
            )

            print(
                f"Change: "
                f"{suggestion.get('suggestion', 'Unknown')}"
            )

            print(
                f"Reason: "
                f"{suggestion.get('reason', 'Unknown')}"
            )

            confidence = suggestion.get(
                "confidence",
                0,
            )

            print(
                f"Confidence: "
                f"{confidence:.2f}"
            )

    else:
        print(
            "- No code change "
            "suggestions were generated"
        )


# ============================================================
# Complete Investigation Output
# ============================================================

def print_investigation(
    investigation,
) -> None:

    print("\n" + "=" * 60)
    print("ADAPTIVEOPS INVESTIGATION")
    print("=" * 60)

    print(
        f"Incident: "
        f"{investigation.incident_id}"
    )

    print(
        f"Service: "
        f"{investigation.service}"
    )

    # --------------------------------------------------------
    # Evidence
    # --------------------------------------------------------

    print("\n--- Evidence ---")

    if investigation.evidence:

        for evidence in investigation.evidence:

            print(
                f"\n[{evidence.type.value}] "
                f"{evidence.signal}"
            )

            print(
                f"Value: "
                f"{evidence.value}"
            )

            print(
                f"Description: "
                f"{evidence.description}"
            )

    else:
        print("- No evidence")

    # --------------------------------------------------------
    # Correlations
    # --------------------------------------------------------

    print("\n--- Correlations ---")

    if investigation.correlations:

        for correlation in (
            investigation.correlations
        ):

            print(
                f"\n"
                f"{correlation.source_evidence_id}"
                f" -> "
                f"{correlation.target_evidence_id}"
            )

            print(
                f"Relationship: "
                f"{correlation.relationship}"
            )

            print(
                f"Confidence: "
                f"{correlation.confidence:.2f}"
            )

    else:
        print("- No correlations")

    # --------------------------------------------------------
    # Timeline
    # --------------------------------------------------------

    print("\n--- Timeline ---")

    if investigation.timeline:

        for event in investigation.timeline:

            print(
                f"\n[{event.event_type}]"
            )

            print(
                event.description
            )

    else:
        print("- No timeline events")

    # --------------------------------------------------------
    # Dependencies
    # --------------------------------------------------------

    print(
        "\n--- Affected Dependencies ---"
    )

    if investigation.affected_dependencies:

        for dependency in (
            investigation.affected_dependencies
        ):
            print(
                f"- {dependency}"
            )

    else:
        print("- None identified")

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print(
        "\n--- Investigation Summary ---"
    )

    print(
        investigation.summary
    )

    # --------------------------------------------------------
    # Uncertainties
    # --------------------------------------------------------

    print("\n--- Uncertainties ---")

    if investigation.uncertainties:

        for uncertainty in (
            investigation.uncertainties
        ):
            print(
                f"- {uncertainty}"
            )

    else:
        print("- None reported")

    # --------------------------------------------------------
    # Repository analysis
    # --------------------------------------------------------

    print_repository_analysis(
        investigation
    )


# ============================================================
# Main Workflow
# ============================================================

async def main() -> None:

    args = build_parser().parse_args()

    print("\n" + "=" * 60)
    print("ADAPTIVEOPS")
    print("=" * 60)

    print(
        f"Project: "
        f"{PROJECT_ID}"
    )

    print(
        f"Service: "
        f"{SERVICE_NAME}"
    )

    print(
        f"Observation Window: "
        f"{OBSERVATION_MINUTES} minutes"
    )

    print(
        f"Repository ID: "
        f"{REPOSITORY_ID}"
    )

    print(
        f"Repository Path: "
        f"{REPOSITORY_PATH}"
    )

    # ========================================================
    # STEP 1 — OBSERVATION
    # ========================================================

    print(
        "\n[1/4] Collecting observation..."
    )

    observation = await ObservationAgent().run(
        project_id=PROJECT_ID,
        service=SERVICE_NAME,
        minutes=OBSERVATION_MINUTES,
    )

    print_observation(
        observation
    )

    # ========================================================
    # Observation-only mode
    # ========================================================

    if args.command == "observation":
        return

    # ========================================================
    # STEP 2 — INCIDENT DETECTION
    # ========================================================

    print(
        "\n[2/4] Detecting incident..."
    )

    incident = IncidentService().detect(
        observation
    )

    if incident is None:

        print(
            "\nNo incident detected."
        )

        return

    print_detection(
        incident
    )

    # ========================================================
    # STEP 3 — BUILD INVESTIGATION CONTEXT
    # ========================================================

    print(
        "\n[3/4] Preparing investigation context..."
    )

    print_investigation_context(
        incident,
        observation,
    )

    # ========================================================
    # STEP 4 — INVESTIGATION
    # ========================================================

    print(
        "\n[4/4] Running investigation..."
    )

    try:

        investigation = (
            await InvestigationService().investigate(
                incident
            )
        )

    except (
        LLMConfigurationError,
        InvestigationWorkflowError,
    ) as error:

        print("\n" + "=" * 60)
        print("ADAPTIVEOPS INVESTIGATION")
        print("=" * 60)

        print("Status: FAILED")

        print(
            f"Error: {error}"
        )

        return

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print_investigation(
        investigation
    )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    asyncio.run(
        main()
    )