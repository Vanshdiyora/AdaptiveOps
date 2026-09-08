import logging

from app.agents.hypothesis import HypothesisAgent
from app.agents.hypothesis.models import HypothesisResult
from app.core.exceptions import InvestigationWorkflowError


logger = logging.getLogger(__name__)


class HypothesisService:
    def __init__(
        self,
        agent: HypothesisAgent | None = None,
    ) -> None:
        self.agent = agent or HypothesisAgent()

    async def generate(
        self,
        investigation_result: dict,
    ) -> HypothesisResult:

        if not investigation_result:
            raise InvestigationWorkflowError(
                "Investigation result is required."
            )

        logger.info("Starting hypothesis generation")

        result = await self.agent.run(
            investigation_result
        )

        logger.info("Hypothesis generation completed")

        return result