from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    incident_id: str
    project_id: str
    service: str

    status: str

    system_state: dict[str, Any]

    observations: list[dict[str, Any]]

    evidence: list[dict[str, Any]]

    hypotheses: list[dict[str, Any]]

    experiments: list[dict[str, Any]]

    root_cause: dict[str, Any]

    proposed_action: dict[str, Any]

    policy_result: dict[str, Any]

    remediation_result: dict[str, Any]

    verification_result: dict[str, Any]

    similar_incidents: list[dict[str, Any]]

    learning_record: dict[str, Any]

    errors: list[str]

    messages: list[Any]