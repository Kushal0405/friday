from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel

from app.events.bus import event_bus

TaskStatus = Literal["QUEUED", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"]


class Task(BaseModel):
    id: str
    name: str
    status: TaskStatus
    progress: float | None = None
    startedAt: str | None = None
    completedAt: str | None = None
    result: str | None = None
    error: str | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskManager:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    async def start(self, name: str) -> Task:
        task = Task(id=str(uuid.uuid4()), name=name, status="RUNNING", startedAt=_now())
        self._tasks[task.id] = task
        await event_bus.publish({"type": "task_started", "task": task.model_dump()})
        return task

    async def complete(self, task_id: str, result: str) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return
        task.status = "COMPLETED"
        task.completedAt = _now()
        task.result = result
        task.progress = 1.0
        await event_bus.publish({"type": "task_completed", "task": task.model_dump()})

    async def fail(self, task_id: str, error: str) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return
        task.status = "FAILED"
        task.completedAt = _now()
        task.error = error
        await event_bus.publish({"type": "task_completed", "task": task.model_dump()})

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)


task_manager = TaskManager()
