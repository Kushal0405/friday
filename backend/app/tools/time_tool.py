from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.tools.base import Tool, ToolResult


class TimeParams(BaseModel):
    pass


class TimeTool(Tool):
    name = "get_time"
    description = "Get the current local date and time on the user's computer."
    parameters = TimeParams

    async def execute(self, params: BaseModel) -> ToolResult:
        now = datetime.now()
        formatted = now.strftime("%A, %B %d, %Y at %I:%M %p")
        return ToolResult(success=True, message=formatted, data={"iso": now.isoformat()})
