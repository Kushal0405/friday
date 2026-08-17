from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.events.bus import event_bus
from app.system.broadcaster import last_known
from app.voice.state_machine import voice_state_machine

router = APIRouter()
logger = get_logger("websocket")


@router.websocket("/ws/friday")
async def friday_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    logger.info("CLIENT CONNECTED")
    queue = event_bus.subscribe()

    # A (re)connecting client has no way to know the current voice state
    # otherwise — voice_state events are only published on transitions, so a
    # client that connects (or reconnects mid-session, e.g. after the backend
    # restarted) without this would default its UI to whatever it last saw,
    # which can desync from the backend's true state and make the mic button
    # send stale actions (e.g. "cancel" when the backend is actually IDLE).
    await websocket.send_text(json.dumps({"type": "voice_state", "state": voice_state_machine.state}))

    for event in last_known.values():
        await websocket.send_text(json.dumps(event))

    async def forward_events() -> None:
        while True:
            event = await queue.get()
            await websocket.send_text(json.dumps(event))

    forward_task = asyncio.create_task(forward_events())

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                continue
            await handle_client_message(message)
    except WebSocketDisconnect:
        logger.info("CLIENT DISCONNECTED")
    finally:
        forward_task.cancel()
        event_bus.unsubscribe(queue)


async def handle_client_message(message: dict) -> None:
    from app.ai.router import command_router
    from app.voice.orchestrator import voice_orchestrator

    msg_type = message.get("type")
    if msg_type == "user_text":
        text = message.get("text", "")
        if text.strip():
            await command_router.handle_text(text)
    elif msg_type == "manual_listen":
        asyncio.create_task(voice_orchestrator.trigger_manual_listen())
    elif msg_type == "cancel":
        logger.info("CANCEL REQUESTED")
        await voice_orchestrator.cancel_current()
    elif msg_type == "confirm":
        logger.info("CONFIRMATION: %s", message)
