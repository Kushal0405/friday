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
        segments, info = model.transcribe(audio, language="en", vad_filter=False)
        segment_list = list(segments)
        text = " ".join(seg.text.strip() for seg in segment_list).strip()
        logger.info(
            "TRANSCRIBE: audio=%.2fs peak=%.4f lang_prob=%.2f segments=%d text=%r",
            len(audio) / 16000,
            float(np.max(np.abs(audio))) if audio.size else 0.0,
            getattr(info, "language_probability", -1.0),
            len(segment_list),
            text,
        )
        return text

    return await asyncio.to_thread(_run)
