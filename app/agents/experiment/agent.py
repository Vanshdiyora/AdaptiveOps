from langchain_core.runnables import Runnable

from app.agents.experiment.prompts import (
    EXPERIMENT_SYSTEM_PROMPT,
)
from app.agents.experiment.schemas import (
    ExperimentPlan,
)


class ExperimentAgent:
    """
    LLM-based experiment planning agent.

    This agent decides WHAT should be tested.
    It does not execute the experiment.
    """

    def __init__(self, llm: Runnable):
        self.llm = llm

    async def generate_plan(
        self,
        hypothesis,
    ) -> ExperimentPlan:

        prompt = self._build_prompt(
            hypothesis
        )

        structured_llm = self.llm.with_structured_output(
            ExperimentPlan
        )

        return await structured_llm.ainvoke(
            prompt
        )

    @staticmethod
    def _build_prompt(
        hypothesis,
    ) -> str:

        return f"""
{EXPERIMENT_SYSTEM_PROMPT}

HYPOTHESIS

Hypothesis ID:
{hypothesis.hypothesis_id}

Hypothesis:
{hypothesis.hypothesis}

Confidence:
{hypothesis.confidence}

Supporting Evidence:
{hypothesis.supporting_evidence}

Contradicting Evidence:
{hypothesis.contradicting_evidence}

Predictions:
{hypothesis.predictions}

Validation Plan:
{getattr(hypothesis, "validation_plan", "")}

Generate the smallest useful set of read-only experiments
required to validate this hypothesis.
"""