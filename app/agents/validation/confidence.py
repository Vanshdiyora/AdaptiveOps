def update_confidence(
    original: float,
    matched_predictions: int,
    contradicted_predictions: int,
    total_predictions: int,
) -> float:

    if total_predictions == 0:
        return original

    support_ratio = (
        matched_predictions / total_predictions
    )

    contradiction_ratio = (
        contradicted_predictions / total_predictions
    )

    delta = (
        support_ratio * 0.20
        - contradiction_ratio * 0.30
    )

    updated = original + delta

    return max(
        0.0,
        min(1.0, updated),
    )