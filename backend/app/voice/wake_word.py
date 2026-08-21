from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.voice.stt import transcribe

logger = get_logger("voice.wake_word")


class WakeWordDetector(ABC):
    @abstractmethod
    async def check(self, audio: np.ndarray) -> bool:
        """Return True if the wake word was heard in this audio segment."""


class WhisperWakeWordDetector(WakeWordDetector):
    """Runs short audio segments through the already-loaded Whisper model
    looking for the configured wake word (fuzzy, case-insensitive substring
    match). Low duty-cycle by design — callers should only call check() on
    segments that already passed a cheap energy-based VAD gate, not on every
    audio block, to avoid transcribing silence continuously.

    This is intentionally swappable: a dedicated lightweight wake-word engine
    (e.g. openWakeWord) can implement the same WakeWordDetector interface
    later without changing any caller."""

    def __init__(self) -> None:
        self._wake_word = settings.wake_word.strip().lower()

    async def check(self, audio: np.ndarray) -> bool:
        text = await transcribe(audio, fast=True)
        heard = self._wake_word in text.lower()
        if heard:
            logger.info("WAKE WORD DETECTED in: %r", text)
        return heard


wake_word_detector: WakeWordDetector = WhisperWakeWordDetector()
