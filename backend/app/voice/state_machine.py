from __future__ import annotations

from typing import Literal

from app.core.logging import get_logger
from app.events.bus import event_bus

logger = get_logger("voice.state")

VoiceState = Literal[
    "IDLE",
    "WAKE_DETECTED",
    "LISTENING",
    "TRANSCRIBING",
    "THINKING",
    "EXECUTING",
    "SPEAKING",
    "ERROR",
    "CANCELLED",
]

VALID_TRANSITIONS: dict[VoiceState, set[VoiceState]] = {
    "IDLE": {"WAKE_DETECTED", "LISTENING"},
    "WAKE_DETECTED": {"LISTENING", "CANCELLED", "IDLE"},
    "LISTENING": {"TRANSCRIBING", "CANCELLED", "IDLE"},
    "TRANSCRIBING": {"THINKING", "ERROR", "IDLE"},
    "THINKING": {"EXECUTING", "SPEAKING", "ERROR", "CANCELLED"},
    "EXECUTING": {"SPEAKING", "ERROR", "CANCELLED"},
    "SPEAKING": {"IDLE", "ERROR"},
    "ERROR": {"IDLE"},
    "CANCELLED": {"IDLE"},
}


class VoiceStateMachine:
    def __init__(self) -> None:
        self._state: VoiceState = "IDLE"

    @property
    def state(self) -> VoiceState:
        return self._state

    async def transition(self, new_state: VoiceState) -> bool:
        allowed = VALID_TRANSITIONS.get(self._state, set())
        if new_state != self._state and new_state not in allowed:
            logger.warning("INVALID TRANSITION: %s -> %s", self._state, new_state)
            return False

        self._state = new_state
        logger.info("VOICE STATE: %s", new_state)
        await event_bus.publish({"type": "voice_state", "state": new_state})
        return True


voice_state_machine = VoiceStateMachine()
