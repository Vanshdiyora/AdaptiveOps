import logging

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable

from app.agents.investigation.agent import InvestigationAgent
from app.agents.investigation.graph import build_investigation_graph
from app.core.exceptions import InvestigationWorkflowError
from app.core.incident_models import Incident, InvestigationResult
from app.llm.provider import LLMUsageTracker, get_investigation_llm
from app.llm.prompts import build_investigation_prompt


logger = logging.getLogger(__name__)


class InvestigationService:

    def __init__(
        self,
        reasoning_chain: Runnable | None = None,
    ):
        self.llm_usage = LLMUsageTracker()

        if reasoning_chain is None:
            try:
                llm = get_investigation_llm(self.llm_usage)
            except Exception:
                llm = None

            parser = JsonOutputParser()

            if llm is not None:
                reasoning_chain = (
                    build_investigation_prompt()
                    | llm
                    | parser
                )
            else:
                reasoning_chain = None

        self.graph = build_investigation_graph(
            InvestigationAgent(reasoning_chain)
        )

    async def investigate(
        self,
        incident: Incident,
    ) -> InvestigationResult:

        logger.info(
            "[LangGraph] Investigation workflow started"
        )

        # Repository path must NOT be added to
        # ObservationSnapshot. Repository configuration
        # belongs to the investigation workflow/settings.

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
        finally:
            logger.info(
                "[LLM] Investigation usage: %s",
                self.llm_usage.summary(),
            )

        if (
            state.get("error")
            or not state.get("investigation_result")
        ):
            raise InvestigationWorkflowError(
                state.get("error")
                or "Investigation produced no result."
            )

        logger.info(
            "[LangGraph] Investigation workflow completed"
        )

        return state["investigation_result"]