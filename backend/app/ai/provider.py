from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from app.ai.base_provider import AIProvider, AIProviderError
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("ai.provider")

__all__ = ["AIProvider", "AIProviderError", "OpenAICompatibleProvider", "ai_provider"]


class OpenAICompatibleProvider(AIProvider):
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            api_key=settings.ai_api_key or "not-needed",
            base_url=settings.ai_base_url,
        )
        self._model = settings.ai_model

    async def chat(
        self,
        messages: list[ChatCompletionMessageParam],
        tools: list[dict[str, Any]] | None = None,
    ) -> Any:
        try:
            kwargs: dict[str, Any] = {"model": self._model, "messages": messages}
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            response = await self._client.chat.completions.create(**kwargs)
            return response.choices[0].message
        except Exception as exc:  # noqa: BLE001 - surface as a typed error to callers
            logger.error("AI PROVIDER ERROR: %s", exc)
            raise AIProviderError(str(exc)) from exc


def _build_provider() -> AIProvider:
    if settings.ai_provider == "anthropic_cli":
        from app.ai.anthropic_cli_provider import AnthropicCLIProvider

        return AnthropicCLIProvider()
    if settings.ai_provider == "race":
        from app.ai.anthropic_cli_provider import AnthropicCLIProvider
        from app.ai.race_provider import RaceProvider

        return RaceProvider([OpenAICompatibleProvider(), AnthropicCLIProvider()])
    return OpenAICompatibleProvider()


ai_provider: AIProvider = _build_provider()
