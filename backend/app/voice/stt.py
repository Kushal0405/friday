from __future__ import annotations

import asyncio

import numpy as np
from faster_whisper import WhisperModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("voice.stt")

_model: WhisperModel | None = None


def _load_model() -> WhisperModel:
    global _model
    if _model is None:
        logger.info("LOADING WHISPER MODEL: %s", settings.whisper_model)
        _model = WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")
        logger.info("WHISPER MODEL READY")
    return _model


async def ensure_model_loaded() -> None:
    await asyncio.to_thread(_load_model)


async def transcribe(audio: np.ndarray) -> str:
    model = await asyncio.to_thread(_load_model)

    def _run() -> str:
        segments, _ = model.transcribe(audio, language="en", vad_filter=False)
        return " ".join(seg.text.strip() for seg in segments).strip()

    return await asyncio.to_thread(_run)
