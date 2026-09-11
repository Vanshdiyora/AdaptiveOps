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


class ExperimentWorkflow:

    def __init__(
        self,
        experiment_agent: ExperimentAgent,
        experiment_service: ExperimentService,
        validation_agent: ValidationAgent,
        validation_service: ValidationService,
    ):
        self.experiment_agent = experiment_agent
        self.experiment_service = experiment_service
        self.validation_agent = validation_agent
        self.validation_service = validation_service

    async def run_experiments(
        self,
        state,
    ):

        hypotheses = state.get(
            "hypotheses",
            [],
        )

        experiments = []
        experiment_results = []

        for hypothesis in hypotheses:

            plan = await self.experiment_agent.generate_plan(
                hypothesis
            )

            for experiment in plan.experiments:

                experiments.append(
                    experiment
                )

                result = (
                    await self.experiment_service.execute(
                        experiment
                    )
                )

                experiment_results.append(
                    result
                )

        return {
            "experiments": experiments,
            "experiment_results": experiment_results,
        }

    async def validate_hypotheses(
        self,
        state,
    ):

        hypotheses = state.get(
            "hypotheses",
            [],
        )

        experiment_results = state.get(
            "experiment_results",
            [],
        )

        validations = []

        for hypothesis in hypotheses:

            relevant_results = [
                result
                for result in experiment_results
                if result.hypothesis_id
                == hypothesis.hypothesis_id
            ]

            validation = (
                await self.validation_agent.validate(
                    hypothesis=hypothesis,
                    experiment_results=relevant_results,
                )
            )

            validation = (
                self.validation_service.finalize(
                    validation
                )
            )

            validations.append(
                validation
            )

        return {
            "validations": validations
        }