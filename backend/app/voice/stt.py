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


async def transcribe(audio: np.ndarray, *, fast: bool = False) -> str:
    """Transcribes audio with faster-whisper.

    `fast=True` is for the wake-word detector, which runs on every candidate
    speech segment while listening (i.e. continuously, on the hot path) and
    only needs to catch a single short word — beam search there just adds
    latency that shows up as the assistant feeling slow to notice its name,
    and can starve the block-draining loop since checks are serialized via
    `_wake_check_busy`. `fast=False` (the default, used for real commands)
    spends more search budget for accuracy since it only runs once per
    command, and enables VAD filtering + disables previous-text conditioning
    to cut down on hallucinated text from trailing silence/noise.
    """
    model = await asyncio.to_thread(_load_model)

    def _run() -> str:
        segments, info = model.transcribe(
            audio,
            language="en",
            beam_size=1 if fast else 5,
            best_of=1 if fast else 5,
            condition_on_previous_text=False,
            vad_filter=not fast,
            vad_parameters=None if fast else dict(min_silence_duration_ms=300),
        )
        segment_list = list(segments)
        text = " ".join(seg.text.strip() for seg in segment_list).strip()
        logger.info(
            "TRANSCRIBE: audio=%.2fs peak=%.4f lang_prob=%.2f segments=%d fast=%s text=%r",
            len(audio) / 16000,
            float(np.max(np.abs(audio))) if audio.size else 0.0,
            getattr(info, "language_probability", -1.0),
            len(segment_list),
            fast,
            text,
        )
        return text

    return await asyncio.to_thread(_run)
