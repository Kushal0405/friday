from __future__ import annotations

import psutil
import win32gui
import win32process

from app.core.logging import get_logger

logger = get_logger("system.active_window")


def get_active_window() -> dict | None:
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None
        title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if not pid:
            return None
        proc = psutil.Process(pid)
        return {"app_name": proc.name(), "title": title}
    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError) as exc:
        logger.warning("ACTIVE WINDOW LOOKUP FAILED: %s", exc)
        return None
