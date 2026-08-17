from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.ai.provider import AIProviderError
from app.ai.router import CommandRouter
from app.events.bus import event_bus


@pytest.mark.asyncio
async def test_handle_text_publishes_transcript_and_response():
    router = CommandRouter()
    queue = event_bus.subscribe()
    try:
        fake_reply = SimpleNamespace(content="Opening Chrome.", tool_calls=None)
        with patch("app.ai.router.ai_provider.chat", new=AsyncMock(return_value=fake_reply)):
            await router.handle_text("open chrome")

        events = [await queue.get() for _ in range(4)]
        types = [e["type"] for e in events]
        assert types == ["transcript", "thinking", "thinking", "assistant_response"]
        assert events[-1]["text"] == "Opening Chrome."
    finally:
        event_bus.unsubscribe(queue)


@pytest.mark.asyncio
async def test_handle_text_publishes_error_when_ai_unavailable():
    router = CommandRouter()
    queue = event_bus.subscribe()
    try:
        with patch(
            "app.ai.router.ai_provider.chat",
            new=AsyncMock(side_effect=AIProviderError("connection refused")),
        ):
            await router.handle_text("open chrome")

        events = [await queue.get() for _ in range(3)]
        types = [e["type"] for e in events]
        assert types == ["transcript", "thinking", "error"]
    finally:
        event_bus.unsubscribe(queue)
