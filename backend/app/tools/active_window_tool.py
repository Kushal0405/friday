from __future__ import annotations

import asyncio

from pydantic import BaseModel

from app.system.active_window import get_active_window
from app.tools.base import Tool, ToolResult


class ActiveWindowParams(BaseModel):
    pass


class ActiveWindowTool(Tool):
    name = "get_active_window"
    description = "Get the name and title of the currently focused application window."
    parameters = ActiveWindowParams

    async def execute(self, params: BaseModel) -> ToolResult:
        window = await asyncio.to_thread(get_active_window)
        if not window:
            return ToolResult(success=False, message="Could not determine the active window.")
        message = f"{window['app_name']} — {window['title']}" if window["title"] else window["app_name"]
        return ToolResult(success=True, message=message, data=window)
