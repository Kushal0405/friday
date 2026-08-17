from __future__ import annotations

import asyncio
import io

import edge_tts
import soundfile as sf
import sounddevice as sd

from app.core.config import settings
from app.core.logging import get_logger
from app.events.bus import event_bus

logger = get_logger("voice.tts")


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
            audio_bytes = await self._synthesize(text)
            if self._stop_requested:
                return
            await asyncio.to_thread(self._play, audio_bytes)
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
