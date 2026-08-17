from __future__ import annotations

import asyncio
import queue
from collections.abc import AsyncIterator

import numpy as np
import sounddevice as sd

from app.core.logging import get_logger

logger = get_logger("voice.capture")

TARGET_SAMPLE_RATE = 16000  # what faster-whisper expects
BLOCK_DURATION_MS = 100


_LOOPBACK_NAME_MARKERS = ("stereo mix", "what u hear", "loopback", "wave out")


# Preferred host API order for callback-mode microphone streaming, most to
# least reliable. Empirically on Windows, PortAudio's MME default device can
# silently deliver near-silent signal in callback mode, and WASAPI callback
# streams measured far quieter here than WASAPI blocking reads (sd.rec) of
# the same device — DirectSound callback streaming measured consistently
# strong. This is a real hardware/driver quirk, not a fixed Windows rule, so
# devices are tried in this preference order rather than hardcoded to one API.
_HOST_API_PREFERENCE = ("Windows DirectSound", "Windows WASAPI", "MME")


def _select_input_device() -> tuple[int, float, int]:
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()
    hostapi_by_name = {h["name"]: i for i, h in enumerate(hostapis)}

    def _mic_priority(name: str) -> int:
        lower = name.lower()
        if "microphone array" in lower:
            return 0
        if "microphone" in lower:
            return 1
        return 2

    for api_name in _HOST_API_PREFERENCE:
        api_index = hostapi_by_name.get(api_name)
        if api_index is None:
            continue
        candidates = [
            (i, d)
            for i, d in enumerate(devices)
            if d["hostapi"] == api_index
            and d["max_input_channels"] > 0
            and not any(marker in d["name"].lower() for marker in _LOOPBACK_NAME_MARKERS)
        ]
        candidates.sort(key=lambda pair: _mic_priority(pair[1]["name"]))
        if candidates:
            i, d = candidates[0]
            channels = min(int(d["max_input_channels"]), 2)
            logger.info(
                "USING %s INPUT DEVICE: %s (%d channel%s)",
                api_name, d["name"], channels, "" if channels == 1 else "s",
            )
            return i, float(d["default_samplerate"]), channels

    default_index = sd.default.device[0]
    default_device = devices[default_index]
    logger.warning("NO PREFERRED INPUT DEVICE FOUND, FALLING BACK TO DEFAULT: %s", default_device["name"])
    return default_index, float(default_device["default_samplerate"]), 1


class MicrophoneStream:
    """Wraps sounddevice's callback-based InputStream as a broadcast source
    of raw float32 mono blocks resampled to 16kHz, the format faster-whisper
    expects.

    Broadcast, not a single shared queue: multiple independent consumers can
    run concurrently (the wake-word loop and an in-progress command listener
    both need live audio at once). A single queue.Queue drained by
    `.get()` from two different async loops would race — each block goes to
    whichever loop happens to call get() first, silently splitting the
    real audio stream between them. Every call to subscribe() gets its own
    queue fed the same blocks instead."""

    def __init__(self) -> None:
        self._subscribers: list[queue.Queue[np.ndarray]] = []
        self._stream: sd.InputStream | None = None
        self._device_index, self._native_rate, self._channels = _select_input_device()
        self._block_size = int(self._native_rate * BLOCK_DURATION_MS / 1000)

    def _callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        if status:
            logger.warning("AUDIO STATUS: %s", status)
        # Array mics expose 2+ capsules; averaging them combines the array
        # instead of discarding all but one capsule. Correlated speech stays
        # strong while uncorrelated per-capsule noise partially cancels,
        # improving SNR versus reading a single channel.
        mono = indata.mean(axis=1) if indata.shape[1] > 1 else indata[:, 0]
        if self._native_rate != TARGET_SAMPLE_RATE:
            target_len = int(len(mono) * TARGET_SAMPLE_RATE / self._native_rate)
            mono = np.interp(
                np.linspace(0, len(mono), target_len, endpoint=False),
                np.arange(len(mono)),
                mono,
            ).astype(np.float32)
        block = mono.copy()
        for q in self._subscribers:
            q.put(block)

    def start(self) -> None:
        self._stream = sd.InputStream(
            device=self._device_index,
            samplerate=self._native_rate,
            channels=self._channels,
            dtype="float32",
            blocksize=self._block_size,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    async def blocks(self) -> AsyncIterator[np.ndarray]:
        q: queue.Queue[np.ndarray] = queue.Queue()
        self._subscribers.append(q)
        loop = asyncio.get_event_loop()
        try:
            while self._stream is not None:
                block = await loop.run_in_executor(None, q.get)
                yield block
        finally:
            self._subscribers.remove(q)


SAMPLE_RATE = TARGET_SAMPLE_RATE
BLOCK_SIZE = int(TARGET_SAMPLE_RATE * BLOCK_DURATION_MS / 1000)


def rms_level(block: np.ndarray) -> float:
    """Root-mean-square amplitude, 0..1, used for both VAD and the HUD's
    real audio_level visualization — never a fake/simulated value."""
    if block.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(block))))
