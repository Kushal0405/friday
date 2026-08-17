from __future__ import annotations

import os
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.tools.base import Tool, ToolResult

logger = get_logger("tools.media")

_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm", ".m4v"}

_SEARCH_ROOTS = [
    Path.home() / "Videos",
    Path.home() / "Downloads",
    Path.home() / "Desktop",
]


def _find_local_video(query: str) -> Path | None:
    needle = query.strip().lower()
    for root in _SEARCH_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in _VIDEO_EXTENSIONS and needle in path.name.lower():
                return path
    return None


class PlayVideoParams(BaseModel):
    query: str = Field(description="Name of a local video file, or a search query/title to play on YouTube")


class PlayVideoTool(Tool):
    name = "play_video"
    description = (
        "Play a video. First searches the user's Videos, Downloads, and "
        "Desktop folders for a matching local file and opens it in the "
        "default player; if no local file matches, opens a YouTube search "
        "for the query in the default browser instead."
    )
    parameters = PlayVideoParams

    async def execute(self, params: BaseModel) -> ToolResult:
        assert isinstance(params, PlayVideoParams)
        local_match = _find_local_video(params.query)

        if local_match:
            try:
                os.startfile(local_match)  # noqa: S606 - resolved via allowlisted search roots above
            except OSError as exc:
                logger.error("FAILED TO PLAY %s: %s", local_match, exc)
                return ToolResult(success=False, message=f"Failed to play {local_match.name}: {exc}")
            return ToolResult(success=True, message=f"Playing {local_match.name}.")

        url = f"https://www.youtube.com/results?search_query={quote_plus(params.query)}"
        webbrowser.open(url)
        return ToolResult(success=True, message=f"No local file found — opened a YouTube search for '{params.query}'.")
