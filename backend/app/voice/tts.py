from __future__ import annotations

import asyncio
import contextlib
import io
import re

import edge_tts
import soundfile as sf
import sounddevice as sd

from app.core.config import settings
from app.core.logging import get_logger
from app.events.bus import event_bus

logger = get_logger("voice.tts")

# Splits a response into sentence-ish chunks so speak() can start playing the
# first one as soon as it's synthesized instead of waiting for the entire
# response to render — the wait for a multi-sentence reply was the biggest
# contributor to output feeling delayed rather than instant.
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _split_into_chunks(text: str) -> list[str]:
    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
    return sentences or [text.strip()]


class TTSService:
    def __init__(self) -> None:
        self._speaking = False
        self._stop_requested = False

    def is_speaking(self) -> bool:
        return self._speaking

    async def speak(self, text: str) -> None:
        if not text.strip():
            return

        self._stop_requested = False
        self._speaking = True
        await event_bus.publish({"type": "tts_state", "speaking": True})

        try:
            # Bounded to 2 so synthesis can run at most one chunk ahead of
            # playback (overlapping network/synthesis latency with playback
            # time) without unboundedly buffering a long response in memory.
            audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=2)

            async def _produce() -> None:
                try:
                    for chunk in _split_into_chunks(text):
                        if self._stop_requested:
                            break
                        audio_bytes = await self._synthesize(chunk)
                        await audio_queue.put(audio_bytes)
                finally:
                    await audio_queue.put(None)

            producer = asyncio.create_task(_produce())
            try:
                while True:
                    audio_bytes = await audio_queue.get()
                    if audio_bytes is None or self._stop_requested:
                        break
                    await asyncio.to_thread(self._play, audio_bytes)
            finally:
                producer.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await producer
        except Exception as exc:  # noqa: BLE001 - TTS failure should not crash the pipeline
            logger.error("TTS FAILED: %s", exc)
        finally:
            self._speaking = False
            await event_bus.publish({"type": "tts_state", "speaking": False})

    async def _synthesize(self, text: str) -> bytes:
        communicate = edge_tts.Communicate(text, settings.tts_voice)
        chunks = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.extend(chunk["data"])
        return bytes(chunks)

    def _play(self, audio_bytes: bytes) -> None:
        data, samplerate = sf.read(io.BytesIO(audio_bytes))
        sd.play(data, samplerate)
        sd.wait()

    def stop(self) -> None:
        self._stop_requested = True
        sd.stop()
        self._speaking = False


tts_service = TTSService()
