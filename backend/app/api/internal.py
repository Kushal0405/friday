"""Loopback-only endpoints used by the MCP server subprocess (app/ai/mcp_server.py)
to report tool execution progress back into the main event bus, since it runs as
a separate process from the FastAPI event loop."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.pipeline_stats import pipeline_stats
from app.tasks.manager import task_manager
from app.events.bus import event_bus

router = APIRouter(prefix="/internal")


class StartTaskRequest(BaseModel):
    name: str


class FinishTaskRequest(BaseModel):
    task_id: str
    success: bool
    message: str


class VoiceConfirmRequest(BaseModel):
    prompt: str


@router.post("/voice-confirm")
async def voice_confirm(body: VoiceConfirmRequest) -> dict:
    """Runs the actual mic-based yes/no prompt in the main backend process
    (which owns the real MicrophoneStream), for tools executing in the MCP
    subprocess where voice_orchestrator would be a separate, mic-less
    instance."""
    from app.voice.orchestrator import voice_orchestrator

    approved = await voice_orchestrator.listen_for_yes_no(body.prompt)
    return {"approved": approved}


@router.post("/start-task")
async def start_task(body: StartTaskRequest) -> dict:
    task = await task_manager.start(body.name)
    pipeline_stats.record_tool_call()
    await event_bus.publish({"type": "tool_started", "tool": body.name, "task_id": task.id})
    return {"task_id": task.id}


@router.post("/finish-task")
async def finish_task(body: FinishTaskRequest) -> dict:
    if body.success:
        await task_manager.complete(body.task_id, body.message)
    else:
        await task_manager.fail(body.task_id, body.message)
    await event_bus.publish(
        {
            "type": "tool_completed",
            "tool": "",
            "task_id": body.task_id,
            "success": body.success,
        }
    )
    return {"ok": True}
