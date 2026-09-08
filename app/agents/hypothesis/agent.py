import logging

from langchain_core.runnables import Runnable

from app.core.exceptions import InvestigationWorkflowError
from app.core.incident_models import InvestigationResult

from .models import HypothesisResult


logger = logging.getLogger(__name__)


class HypothesisAgent:
    """
    Generates competing root-cause hypotheses from
    investigation evidence.
    """

    def __init__(self, reasoning_chain: Runnable):
        self.reasoning_chain = reasoning_chain

    async def generate(
        self,
        investigation_result: InvestigationResult,
    ) -> HypothesisResult:

        if not investigation_result:
            raise InvestigationWorkflowError(
                "Cannot generate hypotheses without investigation evidence."
            )

        try:
            logger.info(
                "[LLM] Hypothesis reasoning started"
            )

            output = await self.reasoning_chain.ainvoke(
                {
                    "investigation": investigation_result
                }
            )

            result = HypothesisResult.model_validate(output)

            logger.info(
                "[LLM] Hypothesis reasoning completed"
            )

            return result

        except InvestigationWorkflowError:
            raise

        except Exception as exc:
            logger.exception(
                "[LLM] Hypothesis reasoning failed"
            )

            raise InvestigationWorkflowError(
                f"Hypothesis generation failed: {exc}"
            ) from exc