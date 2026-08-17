from __future__ import annotations

import asyncio

from pydantic import BaseModel

from app.system.monitor import get_system_stats
from app.tools.base import Tool, ToolResult


class SystemStatusParams(BaseModel):
    pass


class SystemStatusTool(Tool):
    name = "get_system_status"
    description = (
        "Get the current system status: CPU usage, RAM usage, disk usage, "
        "battery level, OS, and uptime."
    )
    parameters = SystemStatusParams

    async def execute(self, params: BaseModel) -> ToolResult:
        stats = await asyncio.to_thread(get_system_stats)
        parts = [f"CPU {stats['cpu']:.0f}%", f"RAM {stats['ram']:.0f}%", f"Disk {stats['disk']:.0f}%"]
        if stats["battery"] is not None:
            parts.append(f"Battery {stats['battery']:.0f}%")
        message = ", ".join(parts)
        return ToolResult(success=True, message=message, data=stats)
