from __future__ import annotations

import asyncio
import difflib
import json
import os
import subprocess
from dataclasses import dataclass

import psutil
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.tools.base import Tool, ToolResult

logger = get_logger("tools.application")

# Name aliases -> what Get-StartApps actually calls it / its exe name, for
# apps whose spoken name doesn't closely match either. Fuzzy matching alone
# handles most cases (e.g. "whatapp" -> "WhatsApp"); this covers the rest.
NAME_ALIASES: dict[str, str] = {
    "vscode": "Visual Studio Code",
    "vs code": "Visual Studio Code",
    "chrome": "Google Chrome",
    "explorer": "File Explorer",
    "file explorer": "File Explorer",
    "calc": "Calculator",
}

# Below this similarity ratio, a voice-transcription typo is treated as "not
# actually this app" rather than risking launching the wrong program.
FUZZY_MATCH_THRESHOLD = 0.6

_APPS_CACHE_TTL_SECONDS = 30


@dataclass
class InstalledApp:
    name: str
    app_id: str


_apps_cache: list[InstalledApp] = []
_apps_cache_time = 0.0


def _list_installed_apps() -> list[InstalledApp]:
    """Enumerates every launchable app the Start Menu knows about — both
    traditional .exe-backed apps and UWP/Microsoft Store apps (which have no
    .exe or Start Menu .lnk file, only an AUMID). This is the same catalog
    Windows' own Start Menu search uses, so anything findable by typing its
    name into Start is findable here too."""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-StartApps | ConvertTo-Json -Compress"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0 or not result.stdout.strip():
        logger.warning("GET-STARTAPPS FAILED: %s", result.stderr)
        return []

    try:
        raw = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    if isinstance(raw, dict):
        raw = [raw]

    return [InstalledApp(name=item["Name"], app_id=item["AppID"]) for item in raw if "Name" in item and "AppID" in item]


def _get_installed_apps_cached() -> list[InstalledApp]:
    global _apps_cache, _apps_cache_time
    import time

    now = time.monotonic()
    if not _apps_cache or (now - _apps_cache_time) > _APPS_CACHE_TTL_SECONDS:
        _apps_cache = _list_installed_apps()
        _apps_cache_time = now
    return _apps_cache


def _find_app(app_name: str) -> InstalledApp | None:
    apps = _get_installed_apps_cached()
    if not apps:
        return None

    query = NAME_ALIASES.get(app_name.strip().lower(), app_name).strip().lower()

    for app in apps:
        if app.name.lower() == query:
            return app

    for app in apps:
        if query in app.name.lower() or app.name.lower() in query:
            return app

    best_match: tuple[float, InstalledApp] | None = None
    for app in apps:
        ratio = difflib.SequenceMatcher(None, query, app.name.lower()).ratio()
        if ratio >= FUZZY_MATCH_THRESHOLD and (best_match is None or ratio > best_match[0]):
            best_match = (ratio, app)

    if best_match:
        logger.info("FUZZY MATCHED APP: %r -> %s (ratio=%.2f)", app_name, best_match[1].name, best_match[0])
        return best_match[1]

    return None


def _launch_app(app: InstalledApp) -> None:
    if app.app_id.lower().endswith(".exe") and os.path.isabs(app.app_id):
        os.startfile(app.app_id)  # noqa: S606 - resolved via Get-StartApps catalog above
        return

    # UWP/Store apps (and simple exe names like "Brave") launch via the
    # virtual shell:AppsFolder namespace using their AUMID.
    subprocess.Popen(
        ["explorer.exe", f"shell:AppsFolder\\{app.app_id}"],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


# Retained for CloseApplicationTool, which matches by running process name
# rather than the Get-StartApps catalog (UWP apps' process names don't
# always match their display name, e.g. WhatsApp -> WhatsApp.exe is fine,
# but this keeps a few well-known short names working without a Get-Process
# round-trip per candidate).
KNOWN_PROCESS_NAMES: dict[str, list[str]] = {
    "chrome": ["chrome.exe"],
    "vscode": ["Code.exe"],
    "vs code": ["Code.exe"],
    "notepad": ["notepad.exe"],
    "calculator": ["CalculatorApp.exe", "calc.exe"],
    "explorer": ["explorer.exe"],
    "file explorer": ["explorer.exe"],
    "word": ["WINWORD.EXE"],
    "excel": ["EXCEL.EXE"],
    "spotify": ["Spotify.exe"],
    "whatsapp": ["WhatsApp.exe", "WhatsApp.Root.exe"],
    "discord": ["Discord.exe"],
    "slack": ["slack.exe"],
    "telegram": ["Telegram.exe"],
}


class OpenApplicationParams(BaseModel):
    app_name: str = Field(description="Name of the application to open, e.g. 'Chrome', 'VS Code', 'WhatsApp'")


class OpenApplicationTool(Tool):
    name = "open_application"
    description = "Open/launch an application on the user's computer by name."
    parameters = OpenApplicationParams

    async def execute(self, params: BaseModel) -> ToolResult:
        assert isinstance(params, OpenApplicationParams)
        app = await asyncio.to_thread(_find_app, params.app_name)

        if not app:
            return ToolResult(
                success=False,
                message=f"Could not find an application called '{params.app_name}'.",
            )

        try:
            await asyncio.to_thread(_launch_app, app)
        except OSError as exc:
            logger.error("FAILED TO LAUNCH %s: %s", app.name, exc)
            return ToolResult(success=False, message=f"Failed to open {app.name}: {exc}")

        return ToolResult(success=True, message=f"Opened {app.name}.")


class CloseApplicationParams(BaseModel):
    app_name: str = Field(description="Name of the application to close, e.g. 'Chrome', 'Notepad'")


class CloseApplicationTool(Tool):
    name = "close_application"
    description = "Close a running application on the user's computer by name."
    parameters = CloseApplicationParams

    async def execute(self, params: BaseModel) -> ToolResult:
        assert isinstance(params, CloseApplicationParams)
        key = params.app_name.strip().lower()
        exe_candidates = [e.lower() for e in KNOWN_PROCESS_NAMES.get(key, [f"{key}.exe"])]

        closed_any = False
        for proc in psutil.process_iter(["name"]):
            try:
                proc_name = (proc.info["name"] or "").lower()
                if proc_name in exe_candidates:
                    proc.terminate()
                    closed_any = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if not closed_any:
            return ToolResult(
                success=False,
                message=f"No running application matching '{params.app_name}' was found.",
            )

        return ToolResult(success=True, message=f"Closed {params.app_name}.")
