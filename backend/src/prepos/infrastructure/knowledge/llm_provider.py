from __future__ import annotations

import re

import structlog

from prepos.application.knowledge.llm_ports import LLMCompletionResult, LLMProviderPort
from prepos.core.config import Settings
from prepos.infrastructure.knowledge.openai_llm_provider import OpenAILLMProvider

logger = structlog.get_logger(__name__)

_CHUNK_ID_PATTERN = re.compile(
    r"chunk_id=([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.IGNORECASE,
)


class DeterministicLLMProvider(LLMProviderPort):
    """Grounded stub LLM for tests and local development without OpenAI chat access."""

    def __init__(self, *, model_name: str = "deterministic-llm") -> None:
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> LLMCompletionResult:
        del system_prompt, temperature, max_tokens
        chunk_ids = _CHUNK_ID_PATTERN.findall(user_prompt)
        if not chunk_ids:
            content = "I don't have enough indexed content to answer confidently."
        else:
            cited = chunk_ids[0]
            content = (
                f"Based on the indexed material, here is a grounded summary. [{cited}]"
            )
        prompt_tokens = max(1, len(user_prompt.split()))
        completion_tokens = max(1, len(content.split()))
        return LLMCompletionResult(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model=self._model_name,
        )


def build_llm_provider(settings: Settings) -> LLMProviderPort:
    if settings.openai_api_key:
        return OpenAILLMProvider(settings)
    logger.warning("openai_api_key_missing_using_deterministic_llm")
    return DeterministicLLMProvider(model_name=settings.llm_model)
