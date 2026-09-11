from time import perf_counter

from app.agents.experiment.schemas import (
    ExperimentRequest,
    ExperimentResult,
    ExperimentObservation,
)
from app.tools.experiment.experiment_tools import (
    ExperimentTools,
)


class ExperimentExecutor:

    def __init__(
        self,
        tools: ExperimentTools | None = None,
    ):
        self.tools = tools or ExperimentTools()

    async def execute(
        self,
        request: ExperimentRequest,
    ) -> ExperimentResult:

        started = perf_counter()

        try:

            result = await self._execute_typed(request)

            observations = self._extract_observations(
                result
            )

            elapsed = (
                perf_counter() - started
            ) * 1000

            return ExperimentResult(
                experiment_id=request.experiment_id,
                hypothesis_id=request.hypothesis_id,
                experiment_type=request.experiment_type,
                target=request.target,
                observations=observations,
                raw_result=result,
                success=True,
                execution_time_ms=elapsed,
            )

        except Exception as exc:

            elapsed = (
                perf_counter() - started
            ) * 1000

            return ExperimentResult(
                experiment_id=request.experiment_id,
                hypothesis_id=request.hypothesis_id,
                experiment_type=request.experiment_type,
                target=request.target,
                observations=[],
                raw_result={},
                success=False,
                error=str(exc),
                execution_time_ms=elapsed,
            )

    async def _execute_typed(
        self,
        request: ExperimentRequest,
    ):

        experiment_type = request.experiment_type
        parameters = request.parameters

        if experiment_type.value == "service_health":

            return await self.tools.check_service_health(
                request.target
            )

        if experiment_type.value == "dependency_latency":

            return await self.tools.query_dependency_latency(
                request.target
            )

        if experiment_type.value == "connection_pool":

            return await self.tools.get_connection_pool_usage(
                request.target
            )

        if experiment_type.value == "error_rate":

            return await self.tools.get_error_rate(
                request.target
            )

        if experiment_type.value == "recent_deployment":

            return await self.tools.get_recent_deployment(
                request.target
            )

        if experiment_type.value == "version_comparison":

            return await self.tools.compare_versions(
                service_id=request.target,
                version_a=parameters["version_a"],
                version_b=parameters["version_b"],
            )

        if experiment_type.value == "metric_comparison":

            return await self.tools.compare_metric(
                metric_name=parameters["metric_name"],
                current_value=parameters["current_value"],
                baseline_value=parameters["baseline_value"],
            )

        if experiment_type.value == "log_pattern":

            return await self.tools.search_log_pattern(
                service_id=request.target,
                pattern=parameters["pattern"],
            )

        raise ValueError(
            f"Unsupported experiment type: {experiment_type}"
        )

    @staticmethod
    def _extract_observations(
        result: dict,
    ) -> list[ExperimentObservation]:

        observations = []

        for key, value in result.items():

            if key in {
                "timestamp",
                "service",
                "dependency",
                "version_a",
                "version_b",
                "pattern",
            }:
                continue

            observations.append(
                ExperimentObservation(
                    name=key,
                    value=value,
                    source="experiment_tool",
                )
            )

        return observations