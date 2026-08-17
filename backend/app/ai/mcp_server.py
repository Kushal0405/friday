"""Stdio MCP server exposing FRIDAY's tool registry to the Claude Code CLI.

Run as a subprocess of `claude -p ... --mcp-config <this>`. Each tool call
executes for real against the OS (same Tool.execute() used by the in-process
router) and reports progress back to the running FastAPI backend over HTTP so
the HUD sees live task/tool events even though this process is separate from
the main event loop.
"""

from __future__ import annotations

import asyncio
import inspect

import httpx
from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from app.core.config import settings
from app.tools import register_all_tools
from app.tools.base import Tool
from app.tools.registry import tool_registry

register_all_tools()

server = MCPServer("friday-tools")
BACKEND_URL = f"http://{settings.friday_host}:{settings.friday_port}"


async def _start_task(tool_name: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.post(f"{BACKEND_URL}/internal/start-task", json={"name": tool_name})
            return resp.json().get("task_id", "")
    except httpx.HTTPError:
        return ""


async def _finish_task(task_id: str, success: bool, message: str) -> None:
    if not task_id:
        return
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                f"{BACKEND_URL}/internal/finish-task",
                json={"task_id": task_id, "success": success, "message": message},
            )
    except httpx.HTTPError:
        pass


def _make_tool_fn(tool: Tool):
    """Build an async function with the tool's real parameter signature (not
    **kwargs) so the MCP SDK's schema introspection sees the actual named
    fields from the tool's Pydantic model instead of a single opaque arg."""

    async def run(**kwargs) -> str:
        task_id = await _start_task(tool.name)
        try:
            params: BaseModel = tool.parameters(**kwargs)
            result = await tool.execute(params)
        except Exception as exc:  # noqa: BLE001 - report any failure as a tool result
            await _finish_task(task_id, success=False, message=str(exc))
            return f"Tool failed: {exc}"

        await _finish_task(task_id, success=result.success, message=result.message)
        return result.message

    parameters = []
    annotations: dict[str, object] = {}
    for field_name, field in tool.parameters.model_fields.items():
        default = inspect.Parameter.empty if field.default is PydanticUndefined else field.default
        parameters.append(
            inspect.Parameter(
                field_name,
                inspect.Parameter.KEYWORD_ONLY,
                default=default,
                annotation=field.annotation,
            )
        )
        annotations[field_name] = field.annotation
    annotations["return"] = str

    run.__signature__ = inspect.Signature(parameters, return_annotation=str)
    run.__name__ = tool.name
    run.__doc__ = tool.description
    run.__annotations__ = annotations
    return run


for _tool in tool_registry.list():
    server.add_tool(_make_tool_fn(_tool), name=_tool.name, description=_tool.description)


if __name__ == "__main__":
    asyncio.run(server.run_stdio_async())
