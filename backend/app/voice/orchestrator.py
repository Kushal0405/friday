from __future__ import annotations

import asyncio
from contextlib import aclosing

import numpy as np

from app.core.logging import get_logger
from app.events.bus import event_bus
from app.voice.capture import BLOCK_SIZE, SAMPLE_RATE, MicrophoneStream, rms_level
from app.voice.state_machine import voice_state_machine
from app.voice.stt import ensure_model_loaded, transcribe
from app.voice.tts import tts_service
from app.voice.wake_word import wake_word_detector

logger = get_logger("voice.orchestrator")

# Energy threshold above which a block counts as "speech" for VAD purposes.
# Lowered from an earlier 0.02 after live testing showed real commands
# peaking around 0.027-0.04 on this hardware — too close to the old
# threshold, so quieter syllables mid-sentence were misread as silence and
# triggered an early cutoff (e.g. "what can you do" captured as only 1.3s
# of audio and mistranscribed).
SPEECH_RMS_THRESHOLD = 0.012
WAKE_WINDOW_SECONDS = 1.5
# Time of continuous sub-threshold audio before we conclude the user is done
# speaking. Raised from 1.2s — that was tight enough to cut off natural
# pauses between words/phrases in a normal sentence.
SILENCE_TIMEOUT_SECONDS = 1.8
MAX_LISTEN_SECONDS = 12


class VoiceOrchestrator:
    def __init__(self) -> None:
        self._mic: MicrophoneStream | None = None
        self._task: asyncio.Task | None = None
        self._enabled = False
        self._cancel_requested = False
        self._activation_lock = asyncio.Lock()
        # Guards against overlapping wake-word checks. A check can take
        # seconds (it runs the full Whisper model); without this, checking
        # blocks the loop that drains the mic queue, so audio backs up and
        # by the time it's processed it's already stale — this is what
        # produced the "laggy / doesn't seem to hear me" symptom.
        self._wake_check_busy = False

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        await ensure_model_loaded()
        self._enabled = True
        self._mic = MicrophoneStream()
        self._mic.start()
        self._task = asyncio.create_task(self._run())
        logger.info("VOICE ORCHESTRATOR STARTED")

    async def stop(self) -> None:
        self._enabled = False
        if self._task:
            self._task.cancel()
        if self._mic:
            self._mic.stop()
            self._mic = None

    async def _run(self) -> None:
        assert self._mic is not None
        wake_buffer: list[np.ndarray] = []
        wake_buffer_blocks = int(WAKE_WINDOW_SECONDS * SAMPLE_RATE / BLOCK_SIZE)

        async for block in self._mic.blocks():
            if not self._enabled:
                break

            level = rms_level(block)
            await event_bus.publish({"type": "audio_level", "level": min(level * 8, 1.0)})

            if voice_state_machine.state != "IDLE":
                continue

            wake_buffer.append(block)
            if len(wake_buffer) > wake_buffer_blocks:
                wake_buffer.pop(0)

            if level < SPEECH_RMS_THRESHOLD:
                continue

            if len(wake_buffer) < wake_buffer_blocks:
                continue

            if self._wake_check_busy:
                # A check is already running (it takes seconds — full
                # Whisper model). Skip scheduling another one rather than
                # piling up background tasks; the loop keeps draining the
                # mic queue in real time regardless, which is the part that
                # actually matters for not feeling laggy.
                continue

            preroll = list(wake_buffer)
            wake_buffer.clear()
            segment = np.concatenate(preroll)
            asyncio.create_task(self._check_wake_word(segment, preroll))

    async def _check_wake_word(self, segment: np.ndarray, preroll: list[np.ndarray]) -> None:
        self._wake_check_busy = True
        try:
            heard = await wake_word_detector.check(segment)
        except Exception as exc:  # noqa: BLE001 - a bad transcription shouldn't kill the loop
            logger.error("WAKE WORD CHECK FAILED: %s", exc)
            return
        finally:
            self._wake_check_busy = False

        if heard and voice_state_machine.state == "IDLE":
            async with self._activation_lock:
                if voice_state_machine.state == "IDLE":
                    await self._handle_activation(skip_wake_state=False, preroll=preroll[-6:])

    async def trigger_manual_listen(self) -> None:
        """Entry point for the HUD's mic button / Ctrl+Alt+Space — starts the
        same LISTENING flow as a spoken wake word, without requiring one."""
        if voice_state_machine.state != "IDLE":
            return
        async with self._activation_lock:
            await self._handle_activation(skip_wake_state=True)

    async def listen_for_yes_no(self, prompt: str) -> bool | None:
        """Speaks a yes/no confirmation prompt and listens for a short spoken
        reply. Returns True/False, or None if nothing usable was heard.
        Used by tools that need explicit voice approval before a destructive
        action (e.g. deleting a file) — runs outside the normal
        wake-word/state-machine flow since it happens mid-tool-call, already
        nested inside EXECUTING."""
        if self._mic is None:
            return None
        await tts_service.speak(prompt)
        transcript = await self._listen_for_command()
        text = transcript.strip().lower()
        if not text:
            return None
        if any(word in text for word in ("yes", "yeah", "yep", "confirm", "sure", "do it")):
            return True
        if any(word in text for word in ("no", "nope", "cancel", "stop", "don't")):
            return False
        return None

    async def cancel_current(self) -> None:
        if voice_state_machine.state in ("IDLE",):
            return
        self._cancel_requested = True
        tts_service.stop()
        await voice_state_machine.transition("CANCELLED")
        await asyncio.sleep(0.1)
        await voice_state_machine.transition("IDLE")
        self._cancel_requested = False

    async def _handle_activation(
        self, skip_wake_state: bool, preroll: list[np.ndarray] | None = None
    ) -> None:
        from app.ai.router import command_router

        if not skip_wake_state:
            await voice_state_machine.transition("WAKE_DETECTED")
        await voice_state_machine.transition("LISTENING")

        transcript = await self._listen_for_command(preroll=preroll)

        if self._cancel_requested:
            return
        if not transcript.strip():
            await voice_state_machine.transition("IDLE")
            return

        await voice_state_machine.transition("TRANSCRIBING")
        await voice_state_machine.transition("THINKING")

        try:
            response_text = await command_router.handle_text(transcript)
        except Exception as exc:  # noqa: BLE001 - keep the voice loop alive on any failure
            logger.error("COMMAND HANDLING FAILED: %s", exc)
            await voice_state_machine.transition("ERROR")
            await asyncio.sleep(1)
            await voice_state_machine.transition("IDLE")
            return

        if self._cancel_requested:
            return

        if response_text:
            await voice_state_machine.transition("SPEAKING")
            await tts_service.speak(response_text)

        if not self._cancel_requested:
            await voice_state_machine.transition("IDLE")

    async def _listen_for_command(self, preroll: list[np.ndarray] | None = None) -> str:
        assert self._mic is not None
        collected: list[np.ndarray] = list(preroll) if preroll else []
        silence_blocks = 0
        silence_limit = int(SILENCE_TIMEOUT_SECONDS * SAMPLE_RATE / BLOCK_SIZE)
        max_blocks = int(MAX_LISTEN_SECONDS * SAMPLE_RATE / BLOCK_SIZE)
        # Preroll already contains the tail of the wake word being spoken, so
        # the mic is proven live — start the silence timer armed rather than
        # waiting for _new_ speech, or a quick trailing command right after
        # the wake word can get cut off before it's ever detected.
        heard_speech = bool(preroll)

        # Explicitly closed via aclosing rather than relying on `break` to
        # tear the generator down: `async for` + `break` does not call the
        # generator's finally block promptly (only on eventual GC), which
        # would leave this call's subscriber queue registered in
        # MicrophoneStream forever — since this runs once per voice command,
        # that's an unbounded, ever-growing leak of abandoned queues each
        # still being fed live audio no one reads.
        async with aclosing(self._mic.blocks()) as block_stream:
            async for block in block_stream:
                if self._cancel_requested:
                    break

                level = rms_level(block)
                await event_bus.publish({"type": "audio_level", "level": min(level * 8, 1.0)})
                collected.append(block)

                if level >= SPEECH_RMS_THRESHOLD:
                    heard_speech = True
                    silence_blocks = 0
                elif heard_speech:
                    silence_blocks += 1

                if (heard_speech and silence_blocks >= silence_limit) or len(collected) >= max_blocks:
                    break

        if not heard_speech or self._cancel_requested:
            return ""

        audio = np.concatenate(collected)
        logger.info(
            "COMMAND AUDIO CAPTURED: %.2fs, peak_rms=%.4f",
            len(audio) / SAMPLE_RATE,
            float(np.max([rms_level(b) for b in collected])) if collected else 0.0,
        )
        return await transcribe(audio)


voice_orchestrator = VoiceOrchestrator()
