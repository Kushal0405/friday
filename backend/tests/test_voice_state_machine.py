from app.events.bus import event_bus
from app.voice.state_machine import VoiceStateMachine


async def test_valid_transition_updates_state_and_publishes_event():
    machine = VoiceStateMachine()
    queue = event_bus.subscribe()
    try:
        result = await machine.transition("LISTENING")
        event = await queue.get()

        assert result is True
        assert machine.state == "LISTENING"
        assert event == {"type": "voice_state", "state": "LISTENING"}
    finally:
        event_bus.unsubscribe(queue)


async def test_invalid_transition_is_rejected():
    machine = VoiceStateMachine()
    # IDLE -> SPEAKING is not a direct valid transition
    result = await machine.transition("SPEAKING")

    assert result is False
    assert machine.state == "IDLE"


async def test_error_can_always_return_to_idle():
    machine = VoiceStateMachine()
    await machine.transition("LISTENING")
    await machine.transition("TRANSCRIBING")
    await machine.transition("ERROR")
    result = await machine.transition("IDLE")

    assert result is True
    assert machine.state == "IDLE"
