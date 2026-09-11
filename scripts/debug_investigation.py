from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from app.agents.investigation.agent import InvestigationAgent
from app.config.settings import settings
from app.core.incident_models import (
    DetectionReason,
    DetectionResult,
    Incident,
    IncidentSeverity,
    IncidentStatus,
)


class DummyMetrics:
    request_count = 250
    error_count = 36
    error_rate = 14.4
    latency_p50_ms = 540
    latency_p95_ms = 1500


class DummyLog:
    def __init__(self, level: str, message: str):
        self.level = level
        self.message = message


class DummyTrace:
    def __init__(self, operation: str, duration_ms: int, status: str):
        self.operation = operation
        self.duration_ms = duration_ms
        self.status = status


class DummyException:
    def __init__(self, exception_type: str, message: str):
        self.exception_type = exception_type
        self.message = message


async def main() -> None:
    repo_path = settings.repository_path or str(Path(__file__).resolve().parents[1])
    observation = type(
        "Observation",
        (),
        {
            "metrics": DummyMetrics(),
            "logs": [DummyLog("ERROR", "Payment request timed out"), DummyLog("WARN", "Retrying payment")],
            "traces": [DummyTrace("POST /payments", 1200, "ERROR")],
            "exceptions": [DummyException("PaymentTimeoutException", "Payment request timed out")],
            "repository_path": repo_path,
        },
    )()

    incident = Incident(
        incident_id="INC-DEMO-001",
        project_id="Investment Research Agent",
        service="payments",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.DETECTED,
        detected_at=datetime.now(timezone.utc),
        trigger=DetectionResult(
            detected=True,
            reasons=[DetectionReason(rule="timeout", message="Payment api timeout", severity=IncidentSeverity.HIGH)],
        ),
        observation=observation,
    )

    agent = InvestigationAgent(reasoning_chain=None)
    repo_result = agent.investigate_repository(incident, repository=repo_path)
    print("\n=== REPOSITORY INVESTIGATION ===")
    print(json.dumps(repo_result, indent=2))

    result = agent.build_code_change_suggestion(repo_result)
    print("\n=== CODE CHANGE SUGGESTION ===")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
