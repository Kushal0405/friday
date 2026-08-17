from __future__ import annotations

import os
from pathlib import Path

import httpx
from pydantic import BaseModel, Field
from send2trash import send2trash

from app.core.config import settings
from app.core.logging import get_logger
from app.tools.base import Tool, ToolResult

logger = get_logger("tools.file")

# Only these user-owned folders are searchable/deletable. Never the FRIDAY
# project itself, Windows/System32, or arbitrary paths the model might
# hallucinate — a misheard filename should be able to hit "wrong file",
# never "wrong drive".
_SAFE_ROOTS = [
    Path.home() / "Desktop",
    Path.home() / "Downloads",
    Path.home() / "Documents",
    Path.home() / "Pictures",
    Path.home() / "Videos",
    Path.home() / "Music",
]


def _resolve_within_safe_roots(file_name: str) -> list[Path]:
    matches: list[Path] = []
    needle = file_name.strip().lower()
    for root in _SAFE_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and needle in path.name.lower():
                matches.append(path)
    return matches


class DeleteFileParams(BaseModel):
    file_name: str = Field(description="Name (or partial name) of the file to delete, e.g. 'report.pdf'")


class DeleteFileTool(Tool):
    name = "delete_file"
    description = (
        "Move a file to the Recycle Bin by name. Only searches the user's "
        "Desktop, Downloads, Documents, Pictures, Videos, and Music folders. "
        "Requires the user's spoken confirmation before deleting — always "
        "ask/confirm before calling this if the request is ambiguous."
    )
    parameters = DeleteFileParams
    requires_confirmation = True

    async def execute(self, params: BaseModel) -> ToolResult:
        assert isinstance(params, DeleteFileParams)
        matches = _resolve_within_safe_roots(params.file_name)

        if not matches:
            return ToolResult(
                success=False,
                message=f"No file matching '{params.file_name}' found in your user folders.",
            )
        if len(matches) > 1:
            listing = ", ".join(m.name for m in matches[:5])
            return ToolResult(
                success=False,
                message=f"Found {len(matches)} files matching '{params.file_name}': {listing}. "
                "Be more specific.",
            )

        target = matches[0]
        approved = await self._confirm(f"Delete {target.name}? Say yes to confirm.")
        if approved is not True:
            return ToolResult(success=False, message=f"Cancelled — {target.name} was not deleted.")

        try:
            send2trash(str(target))
        except OSError as exc:
            logger.error("FAILED TO DELETE %s: %s", target, exc)
            return ToolResult(success=False, message=f"Failed to delete {target.name}: {exc}")

        return ToolResult(success=True, message=f"Moved {target.name} to the Recycle Bin.")

    @staticmethod
    async def _confirm(prompt: str) -> bool | None:
        """Always goes over loopback HTTP to /internal/voice-confirm, even
        when this tool executes in-process — that endpoint is the one place
        guaranteed to run against the main backend's real MicrophoneStream,
        whereas a tool call can also happen inside the MCP subprocess
        (AnthropicCLIProvider) where voice_orchestrator would be a separate,
        mic-less instance."""
        url = f"http://{settings.friday_host}:{settings.friday_port}/internal/voice-confirm"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json={"prompt": prompt})
                return resp.json().get("approved")
        except httpx.HTTPError as exc:
            logger.error("VOICE CONFIRM REQUEST FAILED: %s", exc)
            return None
