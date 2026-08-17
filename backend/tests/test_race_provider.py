import asyncio

import pytest

from app.ai.base_provider import AIProvider, AIProviderError
from app.ai.race_provider import RaceProvider


class _DelayedProvider(AIProvider):
    def __init__(self, delay: float, result=None, error: Exception | None = None):
        self.delay = delay
        self.result = result
        self.error = error
        self.cancelled = False

    async def chat(self, messages, tools=None):
        try:
            await asyncio.sleep(self.delay)
        except asyncio.CancelledError:
            self.cancelled = True
            raise
        if self.error:
            raise self.error
        return self.result


@pytest.mark.asyncio
async def test_returns_fastest_successful_result():
    fast = _DelayedProvider(0.01, result="fast answer")
    slow = _DelayedProvider(0.2, result="slow answer")

    reply = await RaceProvider([slow, fast]).chat([])

    assert reply == "fast answer"


@pytest.mark.asyncio
async def test_cancels_the_loser():
    fast = _DelayedProvider(0.01, result="fast answer")
    slow = _DelayedProvider(0.2, result="slow answer")

    await RaceProvider([slow, fast]).chat([])
    await asyncio.sleep(0.05)

    assert slow.cancelled is True


@pytest.mark.asyncio
async def test_falls_back_to_second_provider_if_first_fails_fast():
    failing = _DelayedProvider(0.01, error=AIProviderError("boom"))
    working = _DelayedProvider(0.05, result="ok")

    reply = await RaceProvider([failing, working]).chat([])

    assert reply == "ok"


@pytest.mark.asyncio
async def test_raises_when_all_providers_fail():
    a = _DelayedProvider(0.01, error=AIProviderError("a failed"))
    b = _DelayedProvider(0.02, error=AIProviderError("b failed"))

    with pytest.raises(AIProviderError):
        await RaceProvider([a, b]).chat([])
