"""Fires both configured AI providers concurrently and returns whichever
responds first, cancelling the other. Used when AI_PROVIDER=race.

Trade-off: the losing provider is cancelled immediately, even if it had
already started executing a real tool (e.g. Claude's CLI mid-flight via
MCP). That's a deliberate choice for responsiveness over letting a stray
background action finish — see build plan notes for the reasoning.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.ai.base_provider import AIProvider, AIProviderError
from app.core.logging import get_logger

logger = get_logger("ai.race")


class RaceProvider(AIProvider):
    def __init__(self, providers: list[AIProvider]) -> None:
        if not providers:
            raise ValueError("RaceProvider needs at least one underlying provider")
        self._providers = providers
        self.last_winner: str | None = None

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> Any:
        task_names = {}
        pending = set()
        for p in self._providers:
            task = asyncio.create_task(p.chat(messages, tools))
            task_names[task] = type(p).__name__
            pending.add(task)
        errors: list[BaseException] = []

        try:
            while pending:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    exc = task.exception()
                    if exc is None:
                        self.last_winner = task_names[task]
                        logger.info("RACE WINNER: %s", task_names[task])
                        return task.result()
                    errors.append(exc)
        finally:
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)

        logger.error("ALL RACE PROVIDERS FAILED: %s", errors)
        raise AIProviderError(f"All AI providers failed: {errors[0]}" if errors else "All AI providers failed")
