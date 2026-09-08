import logging

from langchain_groq import ChatGroq

from app.config.settings import settings
from app.core.exceptions import LLMConfigurationError


logger = logging.getLogger(__name__)


def get_investigation_llm() -> ChatGroq:
    if not settings.groq_api_key:
        raise LLMConfigurationError(
            "GROQ_API_KEY is required."
        )

    logger.info("[LLM] Provider: Groq")
    logger.info("[LLM] Model: %s", settings.groq_model)

    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=settings.groq_temperature,
        reasoning_format="hidden",
        reasoning_effort="none",
        max_tokens=1000,
        timeout=60,
        max_retries=1,
    )