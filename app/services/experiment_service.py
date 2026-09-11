import time

from app.agents.experiment.schemas import (
    ExperimentRequest,
    ExperimentResult,
    ExperimentObservation,
)
from app.tools.experiment.experiment_tools import (
    ExperimentTools,
)


class ExperimentService:

    def __init__(
        self,
        tools: ExperimentTools | None = None,
    ):
        self.tools = tools or ExperimentTools()

    async def execute(
        self,
        request: ExperimentRequest,
    ) -> ExperimentResult:

        started = time.perf_counter()

        try:

            raw_result = await self._execute(
                request
            )

            observations = self._to_observations(
                raw_result
            )

            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000

            return ExperimentResult(
                experiment_id=request.experiment_id,
                hypothesis_id=request.hypothesis_id,
                experiment_type=request.experiment_type,
                target=request.target,
                success=True,
                observations=observations,
                raw_result=raw_result,
                execution_time_ms=elapsed_ms,
            )

        except Exception as exc:

            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000

            return ExperimentResult(
                experiment_id=request.experiment_id,
                hypothesis_id=request.hypothesis_id,
                experiment_type=request.experiment_type,
                target=request.target,
                success=False,
                error=str(exc),
                execution_time_ms=elapsed_ms,
            )

    async def _execute(
        self,
        request: ExperimentRequest,
    ) -> dict:

        experiment_type = (
            request.experiment_type.value
        )

        parameters = request.parameters

        if experiment_type == "service_health":

            return await self.tools.check_service_health(
                request.target
            )

        if experiment_type == "dependency_latency":

            return await self.tools.query_dependency_latency(
                request.target
            )

        if experiment_type == "connection_pool":

            return await self.tools.get_connection_pool_usage(
                request.target
            )

        if experiment_type == "error_rate":

            return await self.tools.get_error_rate(
                request.target
            )

        if experiment_type == "recent_deployment":

            return await self.tools.get_recent_deployment(
                request.target
            )

        if experiment_type == "version_comparison":

            return await self.tools.compare_versions(
                service_id=request.target,
                version_a=parameters["version_a"],
                version_b=parameters["version_b"],
            )

        if experiment_type == "metric_comparison":

            return await self.tools.compare_metric(
                metric_name=parameters["metric_name"],
                current_value=parameters["current_value"],
                baseline_value=parameters["baseline_value"],
            )

        if experiment_type == "log_pattern":

            return await self.tools.search_log_pattern(
                service_id=request.target,
                pattern=parameters["pattern"],
            )

        raise ValueError(
            f"Unsupported experiment type: {experiment_type}"
        )

    @staticmethod
    def _to_observations(
        result: dict,
    ) -> list[ExperimentObservation]:

        ignored_fields = {
            "timestamp",
            "service",
            "dependency",
            "metric",
            "pattern",
            "version_a",
            "version_b",
        }

        observations = []

        for name, value in result.items():

            if name in ignored_fields:
                continue

            observations.append(
                ExperimentObservation(
                    name=name,
                    value=value,
                    timestamp=result.get("timestamp"),
                )
            )

        return observations