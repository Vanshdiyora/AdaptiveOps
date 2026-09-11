from langchain_core.runnables import Runnable

from app.agents.validation.prompts import (
    VALIDATION_SYSTEM_PROMPT,
)
from app.agents.validation.schemas import (
    ValidationResult,
)


class ValidationAgent:
    """
    Determines whether experiment observations support
    or contradict a hypothesis.
    """

    def __init__(self, llm: Runnable):
        self.llm = llm

    async def validate(
        self,
        hypothesis,
        experiment_results,
    ) -> ValidationResult:

        prompt = self._build_prompt(
            hypothesis,
            experiment_results,
        )

        structured_llm = self.llm.with_structured_output(
            ValidationResult,
            method="json_mode",
        )

        return await structured_llm.ainvoke(
            prompt
        )

    @staticmethod
    def _build_prompt(
        hypothesis,
        experiment_results,
    ) -> str:

        results = []

        for result in experiment_results:

            results.append(
                {
                    "experiment_id": result.experiment_id,
                    "experiment_type": (
                        result.experiment_type.value
                        if hasattr(
                            result.experiment_type,
                            "value",
                        )
                        else result.experiment_type
                    ),
                    "target": result.target,
                    "success": result.success,
                    "observations": [
                        observation.model_dump()
                        for observation
                        in result.observations
                    ],
                    "raw_result": result.raw_result,
                    "error": result.error,
                }
            )

        return f"""
{VALIDATION_SYSTEM_PROMPT}

HYPOTHESIS

ID:
{hypothesis.hypothesis_id}

Description:
{hypothesis.hypothesis}

Original Confidence:
{hypothesis.confidence}

Predictions:
{hypothesis.predictions}

Supporting Evidence:
{hypothesis.supporting_evidence}

Contradicting Evidence:
{hypothesis.contradicting_evidence}


EXPERIMENT RESULTS

{results}


TASK

Evaluate every prediction against the actual experiment
observations.

For each prediction:

1. Identify what was expected.
2. Identify what was observed.
3. Determine whether the prediction matched.
4. Explain the result.
5. Determine whether evidence supports or contradicts
   the hypothesis.

Important:

- Never invent observations.
- Missing observations are not automatically contradictions.
- Strong contradictory evidence should reduce confidence.
- Supporting evidence should increase confidence.
- Do not recommend remediation.
- Do not claim certainty without sufficient evidence.
"""