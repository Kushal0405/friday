from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AIProviderError(Exception):
    """Raised when the configured AI provider is unreachable or errors."""


class AIProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> Any:
        """Send a chat completion request, optionally offering tool schemas.
        Returns the raw provider response message (may include tool_calls)."""
