from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.core.incident_models import Incident, IncidentSeverity, IncidentStatus, DetectionResult, DetectionReason
from app.agents.investigation.agent import InvestigationAgent


@pytest.fixture
def sample_incident() -> Incident:
    return Incident(
        incident_id="INC-1",
        project_id="proj",
        service="payments",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.DETECTED,
        detected_at=datetime.now(timezone.utc),
        trigger=DetectionResult(
            detected=True,
            reasons=[DetectionReason(rule="timeout", message="Payment request timed out", severity=IncidentSeverity.HIGH)],
        ),
        observation={
            "metrics": type("Metrics", (), {"request_count": 120, "error_count": 30, "error_rate": 25, "latency_p50_ms": 500, "latency_p95_ms": 1500})(),
            "logs": [],
            "traces": [],
            "exceptions": [type("ExceptionItem", (), {"exception_type": "PaymentTimeoutException", "message": "Payment request timed out"})()],
        },
    )


def test_investigation_without_repository(sample_incident):
    agent = InvestigationAgent(reasoning_chain=None)
    result = agent.investigate_repository(sample_incident, repository=None)
    assert result["code_evidence"] == []
    assert result["code_findings"] == []


def test_investigation_with_repository(sample_incident, tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    src = repo / "src"
    src.mkdir()
    (src / "payment_service.py").write_text(
        "def process_payment():\n    try:\n        return call_payment()\n    except PaymentTimeoutException:\n        raise\n",
        encoding="utf-8",
    )

    agent = InvestigationAgent(reasoning_chain=None)
    result = agent.investigate_repository(sample_incident, repository=repo)
    assert result["code_evidence"]
    assert any("process_payment" in item["reason"] for item in result["code_evidence"])
    assert result["code_findings"]


def test_code_change_suggestion_generation(sample_incident, tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    src = repo / "src"
    src.mkdir()
    (src / "payment_service.py").write_text(
        "def process_payment():\n    return call_payment()\n",
        encoding="utf-8",
    )

    agent = InvestigationAgent(reasoning_chain=None)
    result = agent.investigate_repository(sample_incident, repository=repo)
    suggestion = agent.build_code_change_suggestion(result)
    assert suggestion["file"]
    assert suggestion["problem"]
    assert suggestion["suggestion"]
