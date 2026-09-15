import logging
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_openai import ChatOpenAI

from app.config.settings import settings
from app.core.exceptions import LLMConfigurationError


logger = logging.getLogger(__name__)


class LLMUsageTracker(BaseCallbackHandler):
    """Collect LLM call and token totals for one workflow execution."""

    def __init__(self) -> None:
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0

    def on_llm_start(self, *args: Any, **kwargs: Any) -> None:
        self.calls += 1

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        usage = self._extract_usage(response)
        input_tokens, output_tokens, total_tokens = self._token_counts(usage)

        self.input_tokens += int(input_tokens or 0)
        self.output_tokens += int(output_tokens or 0)
        self.total_tokens += int(
            total_tokens or ((input_tokens or 0) + (output_tokens or 0))
        )

    @staticmethod
    def _extract_usage(response: LLMResult) -> dict[str, Any]:
        usage = dict(response.llm_output or {}).get("token_usage", {})
        if usage:
            return usage

        for generation_group in response.generations:
            for generation in generation_group:
                message_usage = getattr(
                    getattr(generation, "message", None),
                    "usage_metadata",
                    None,
                )
                if message_usage:
                    return dict(message_usage)
        return {}

    @staticmethod
    def _token_counts(usage: dict[str, Any]) -> tuple[int, int, int]:
        input_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
        output_tokens = usage.get(
            "completion_tokens",
            usage.get("output_tokens", 0),
        )
        total_tokens = usage.get("total_tokens", 0)
        return int(input_tokens or 0), int(output_tokens or 0), int(total_tokens or 0)

    def summary(self) -> str:
        return (
            f"calls={self.calls}, input_tokens={self.input_tokens}, "
            f"output_tokens={self.output_tokens}, total_tokens={self.total_tokens}"
        )


def get_investigation_llm(
    usage_tracker: LLMUsageTracker | None = None,
) -> ChatOpenAI:
    if not settings.maq_api_key:
        raise LLMConfigurationError(
            "MAQ_API_KEY is required."
        )

    logger.info("[LLM] Provider: MAQ AI")
    logger.info("[LLM] Model: %s", settings.maq_model)

    llm_kwargs: dict[str, Any] = {
        "api_key": settings.maq_api_key,
        "base_url": settings.maq_base_url,
        "model": settings.maq_model,
        "temperature": settings.maq_temperature,
        "max_tokens": 40000,
        "timeout": 600,
        "max_retries": 3,
    }
    if usage_tracker is not None:
        llm_kwargs["callbacks"] = [usage_tracker]

    return ChatOpenAI(
        **llm_kwargs,
    )