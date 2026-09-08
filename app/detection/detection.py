from app.core.incident_models import (
    DetectionReason,
    DetectionResult,
    IncidentSeverity,
)
from app.detection.rules import (
    ERROR_RATE_CRITICAL,
    ERROR_RATE_DEGRADED,
    P95_LATENCY_CRITICAL,
    REDIS_POOL_WARNING,
)


class DetectionEngine:

    def detect(self, observation) -> DetectionResult:

        reasons = []

        metrics = observation.metrics

        # -----------------------------------------
        # Error Rate
        # -----------------------------------------

        if metrics.error_rate >= ERROR_RATE_CRITICAL:

            reasons.append(
                DetectionReason(
                    rule="ERROR_RATE_CRITICAL",
                    message=(
                        f"Error rate is "
                        f"{metrics.error_rate}% "
                        f"which exceeds the critical "
                        f"threshold of "
                        f"{ERROR_RATE_CRITICAL}%."
                    ),
                    severity=IncidentSeverity.CRITICAL,
                )
            )

        elif metrics.error_rate >= ERROR_RATE_DEGRADED:

            reasons.append(
                DetectionReason(
                    rule="ERROR_RATE_DEGRADED",
                    message=(
                        f"Error rate is "
                        f"{metrics.error_rate}% "
                        f"which exceeds the degraded "
                        f"threshold of "
                        f"{ERROR_RATE_DEGRADED}%."
                    ),
                    severity=IncidentSeverity.MEDIUM,
                )
            )

        # -----------------------------------------
        # P95 Latency
        # -----------------------------------------

        if metrics.latency_p95_ms >= P95_LATENCY_CRITICAL:

            reasons.append(
                DetectionReason(
                    rule="P95_LATENCY_CRITICAL",
                    message=(
                        f"P95 latency is "
                        f"{metrics.latency_p95_ms}ms "
                        f"which exceeds the critical "
                        f"threshold of "
                        f"{P95_LATENCY_CRITICAL}ms."
                    ),
                    severity=IncidentSeverity.CRITICAL,
                )
            )

        # -----------------------------------------
        # Redis indicators
        # -----------------------------------------

        for log in observation.logs:

            message = log.message.lower()

            if (
                "redis connection pool utilization"
                in message
                and "80%" in message
            ):

                reasons.append(
                    DetectionReason(
                        rule="REDIS_POOL_HIGH",
                        message=(
                            "Redis connection pool "
                            "utilization is above "
                            f"{REDIS_POOL_WARNING}%."
                        ),
                        severity=IncidentSeverity.HIGH,
                    )
                )

        # -----------------------------------------
        # No incident
        # -----------------------------------------

        if not reasons:

            return DetectionResult(
                detected=False
            )

        # -----------------------------------------
        # Determine highest severity
        # -----------------------------------------

        priority = {
            IncidentSeverity.LOW: 1,
            IncidentSeverity.MEDIUM: 2,
            IncidentSeverity.HIGH: 3,
            IncidentSeverity.CRITICAL: 4,
        }

        severity = max(
            (
                reason.severity
                for reason in reasons
            ),
            key=lambda value: priority[value]
        )

        return DetectionResult(
            detected=True,
            severity=severity,
            reasons=reasons,
        )