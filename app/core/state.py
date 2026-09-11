from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    # ---------------------------------------------------------
    # Incident Context
    # ---------------------------------------------------------

    incident_id: str
    project_id: str
    service: str

    status: str

    # ---------------------------------------------------------
    # System Context
    # ---------------------------------------------------------

    system_state: dict[str, Any]

    # ---------------------------------------------------------
    # Observation / Investigation
    # ---------------------------------------------------------

    observations: list[dict[str, Any]]

    evidence: list[dict[str, Any]]
    repository_path: str | None
    code_evidence: list[dict[str, Any]]
    code_findings: list[dict[str, Any]]
    code_change_suggestions: list[dict[str, Any]]

    # ---------------------------------------------------------
    # Hypothesis
    # ---------------------------------------------------------

    hypotheses: list[dict[str, Any]]

    # ---------------------------------------------------------
    # Experiment
    # ---------------------------------------------------------

    experiments: list[dict[str, Any]]

    experiment_results: list[dict[str, Any]]

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    validations: list[dict[str, Any]]

    # ---------------------------------------------------------
    # Root Cause / Decision
    # ---------------------------------------------------------

    root_cause: dict[str, Any]

    proposed_action: dict[str, Any]

    # ---------------------------------------------------------
    # Safety / Policy
    # ---------------------------------------------------------

    policy_result: dict[str, Any]

    # ---------------------------------------------------------
    # Remediation
    # ---------------------------------------------------------

    remediation_result: dict[str, Any]

    # ---------------------------------------------------------
    # Verification
    # ---------------------------------------------------------

    verification_result: dict[str, Any]

    # ---------------------------------------------------------
    # Operational Memory / Learning
    # ---------------------------------------------------------

    similar_incidents: list[dict[str, Any]]

    learning_record: dict[str, Any]

    # ---------------------------------------------------------
    # Errors / Messages
    # ---------------------------------------------------------

    errors: list[str]

    messages: list[Any]