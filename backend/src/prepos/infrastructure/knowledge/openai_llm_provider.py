from __future__ import annotations

import httpx
import structlog

from prepos.application.knowledge.llm_ports import LLMCompletionResult, LLMProviderPort
from prepos.core.config import Settings
from prepos.core.exceptions import ValidationError

logger = structlog.get_logger(__name__)


class OpenAILLMProvider(LLMProviderPort):
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValidationError("OPENAI_API_KEY is required for knowledge generation.")
        self._settings = settings
        self._api_key = settings.openai_api_key

    @property
    def model_name(self) -> str:
        return self._settings.llm_model

    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> LLMCompletionResult:
        token_limit = max_tokens or self._settings.llm_max_completion_tokens
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "temperature": temperature,
                    "max_tokens": token_limit,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
            )
            response.raise_for_status()
            payload = response.json()

        choices = payload.get("choices", [])
        if not isinstance(choices, list) or not choices:
            raise ValidationError("Unexpected chat completion response from OpenAI.")

        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        content = str(message.get("content", "")).strip()
        if not content:
            raise ValidationError("OpenAI returned an empty completion.")

        usage = payload.get("usage", {}) if isinstance(payload.get("usage"), dict) else {}
        return LLMCompletionResult(
            content=content,
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
            model=str(payload.get("model", self.model_name)),
        )
