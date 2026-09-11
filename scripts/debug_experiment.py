import asyncio
import json

from app.agents.experiment.agent import (
    ExperimentAgent,
)
from app.agents.validation.agent import (
    ValidationAgent,
)
from app.services.experiment_service import (
    ExperimentService,
)
from app.services.validation_service import (
    ValidationService,
)
from app.tools.experiment.experiment_tools import (
    ExperimentTools,
)
from app.llm.provider import get_investigation_llm


class MockHypothesis:

    hypothesis_id = "H1"

    hypothesis = (
        "Redis connection exhaustion"
    )

    confidence = 0.84

    supporting_evidence = [
        "Redis timeout exceptions increased",
        "Connection pool utilization above 80%",
        "Redis spans are slow",
    ]

    contradicting_evidence = []

    predictions = [
        "Redis dependency latency should be elevated",
        "Connection acquisition failures should increase",
        "Connection pool utilization should be high",
    ]

    validation_plan = (
        "Check Redis latency and connection pool usage."
    )


async def main():

    llm = get_investigation_llm()

    experiment_agent = ExperimentAgent(
        llm=llm
    )

    validation_agent = ValidationAgent(
        llm=llm
    )

    experiment_service = ExperimentService(
        tools=ExperimentTools()
    )

    validation_service = ValidationService()

    hypothesis = MockHypothesis()

    print(
        "\n=== EXPERIMENT PLAN ===\n"
    )

    plan = await experiment_agent.generate_plan(
        hypothesis
    )

    print(
        json.dumps(
            plan.model_dump(),
            indent=2,
        )
    )

    results = []

    print(
        "\n=== EXPERIMENT RESULTS ===\n"
    )

    for experiment in plan.experiments:

        result = (
            await experiment_service.execute(
                experiment
            )
        )

        results.append(result)

        print(
            json.dumps(
                result.model_dump(),
                indent=2,
                default=str,
            )
        )

    print(
        "\n=== VALIDATION ===\n"
    )

    validation = await validation_agent.validate(
        hypothesis=hypothesis,
        experiment_results=results,
    )

    validation = (
        validation_service.finalize(
            validation
        )
    )

    print(
        json.dumps(
            validation.model_dump(),
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())