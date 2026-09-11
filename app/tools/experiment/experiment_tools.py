from datetime import datetime, timezone
from typing import Any


class ExperimentTools:
    """
    Read-only experiment tools.

    These currently use deterministic mock data.
    Later they can call Application Insights, Prometheus,
    OpenTelemetry, Kubernetes, Azure, etc.
    """

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    async def check_service_health(
        self,
        service_id: str,
    ) -> dict[str, Any]:

        return {
            "service": service_id,
            "status": "DEGRADED",
            "error_rate": 0.148,
            "p95_latency_ms": 2450,
            "cpu_percent": 62.4,
            "memory_percent": 71.2,
            "timestamp": self._timestamp(),
        }

    async def query_dependency_latency(
        self,
        dependency_id: str,
    ) -> dict[str, Any]:

        return {
            "dependency": dependency_id,
            "p50_latency_ms": 120,
            "p95_latency_ms": 1850,
            "p99_latency_ms": 4200,
            "error_rate": 0.092,
            "timestamp": self._timestamp(),
        }

    async def get_connection_pool_usage(
        self,
        service_id: str,
    ) -> dict[str, Any]:

        return {
            "service": service_id,
            "pool_size": 100,
            "active_connections": 92,
            "utilization_percent": 92.0,
            "connection_failures": 38,
            "timestamp": self._timestamp(),
        }

    async def get_error_rate(
        self,
        service_id: str,
    ) -> dict[str, Any]:

        return {
            "service": service_id,
            "error_rate": 0.148,
            "baseline_error_rate": 0.012,
            "timestamp": self._timestamp(),
        }

    async def get_recent_deployment(
        self,
        service_id: str,
    ) -> dict[str, Any]:

        return {
            "service": service_id,
            "deployment_found": True,
            "current_version": "v2.4.1",
            "previous_version": "v2.4.0",
            "deployed_minutes_ago": 23,
            "timestamp": self._timestamp(),
        }

    async def compare_versions(
        self,
        service_id: str,
        version_a: str,
        version_b: str,
    ) -> dict[str, Any]:

        return {
            "service": service_id,
            "version_a": version_a,
            "version_b": version_b,

            "version_a_error_rate": 0.011,
            "version_b_error_rate": 0.148,

            "version_a_p95_latency_ms": 320,
            "version_b_p95_latency_ms": 2450,

            "timestamp": self._timestamp(),
        }

    async def compare_metric(
        self,
        metric_name: str,
        current_value: float,
        baseline_value: float,
    ) -> dict[str, Any]:

        delta = current_value - baseline_value

        percentage_change = (
            (delta / baseline_value) * 100
            if baseline_value != 0
            else 0.0
        )

        return {
            "metric": metric_name,
            "current_value": current_value,
            "baseline_value": baseline_value,
            "delta": delta,
            "percentage_change": percentage_change,
            "timestamp": self._timestamp(),
        }

    async def search_log_pattern(
        self,
        service_id: str,
        pattern: str,
    ) -> dict[str, Any]:

        return {
            "service": service_id,
            "pattern": pattern,
            "matches": 42,
            "baseline_matches": 3,
            "timestamp": self._timestamp(),
        }