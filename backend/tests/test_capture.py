import asyncio
from contextlib import aclosing

import numpy as np
import pytest

from app.voice.capture import MicrophoneStream


@pytest.fixture
def stream(monkeypatch):
    monkeypatch.setattr(
        "app.voice.capture._select_input_device", lambda: (0, 16000.0, 1)
    )
    mic = MicrophoneStream.__new__(MicrophoneStream)
    mic._subscribers = []
    mic._stream = object()  # sentinel so blocks() keeps looping
    mic._device_index, mic._native_rate, mic._channels = 0, 16000.0, 1
    mic._block_size = 1600
    return mic


async def test_two_concurrent_consumers_each_receive_every_block(stream):
    received_a: list[np.ndarray] = []
    received_b: list[np.ndarray] = []

    async def consume(target: list[np.ndarray], count: int):
        async for block in stream.blocks():
            target.append(block)
            if len(target) >= count:
                break

    task_a = asyncio.create_task(consume(received_a, 3))
    task_b = asyncio.create_task(consume(received_b, 3))
    await asyncio.sleep(0.05)  # let both subscribe before blocks are pushed

    fake_frames = np.array([[0.1], [0.2], [0.3]], dtype=np.float32)
    for _ in range(3):
        stream._callback(fake_frames, 3, None, None)

    await asyncio.wait_for(asyncio.gather(task_a, task_b), timeout=2)

    assert len(received_a) == 3
    assert len(received_b) == 3
    # Both consumers got the same real blocks, not a split subset of them.
    for a, b in zip(received_a, received_b):
        assert np.array_equal(a, b)


async def test_unsubscribing_stops_receiving_future_blocks(stream):
    received: list[np.ndarray] = []

    async def consume():
        async with aclosing(stream.blocks()) as block_stream:
            async for block in block_stream:
                received.append(block)
                return

    task = asyncio.create_task(consume())
    await asyncio.sleep(0.05)

    fake_frames = np.array([[0.5]], dtype=np.float32)
    stream._callback(fake_frames, 1, None, None)
    await asyncio.wait_for(task, timeout=2)

    assert len(stream._subscribers) == 0
