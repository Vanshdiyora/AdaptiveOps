import logging
import json

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable

from app.agents.investigation.agent import InvestigationAgent
from app.agents.investigation.graph import build_investigation_graph
from app.core.exceptions import InvestigationWorkflowError
from app.core.incident_models import Incident, InvestigationResult
from app.llm.provider import get_investigation_llm
from app.llm.prompts import build_investigation_prompt
from app.llm.structured_output import InvestigationLLMOutput


logger = logging.getLogger(__name__)


class InvestigationService:

    def __init__(self, reasoning_chain: Runnable | None = None):

        if reasoning_chain is None:
            llm = get_investigation_llm()
            parser = JsonOutputParser()

            reasoning_chain = (
                build_investigation_prompt()
                | llm
                | parser
            )

        self.graph = build_investigation_graph(
            InvestigationAgent(reasoning_chain)
        )

    async def investigate(
        self,
        incident: Incident,
    ) -> InvestigationResult:

        logger.info("[LangGraph] Investigation workflow started")

        try:
            state = await self.graph.ainvoke(
                {
                    "incident": incident,
                    "error": None,
                }
            )

        except Exception as error:
            raise InvestigationWorkflowError(
                f"Investigation graph failed: {error}"
            ) from error

        if state.get("error") or not state.get("investigation_result"):
            raise InvestigationWorkflowError(
                state.get("error")
                or "Investigation produced no result."
            )

        logger.info("[LangGraph] Investigation workflow completed")

        return state["investigation_result"]