from __future__ import annotations

import asyncio
import json
import re

from app.core.logging import get_logger

logger = get_logger("system.security")

_DOTNET_DATE_RE = re.compile(r"/Date\((\d+)\)/")


async def _run_powershell(command: str) -> str | None:
    try:
        proc = await asyncio.create_subprocess_exec(
            "powershell",
            "-NoProfile",
            "-Command",
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
        if proc.returncode != 0:
            logger.warning("POWERSHELL FAILED: %s", stderr.decode(errors="ignore"))
            return None
        return stdout.decode(errors="ignore").strip()
    except (asyncio.TimeoutError, OSError) as exc:
        logger.warning("POWERSHELL ERROR: %s", exc)
        return None


async def get_defender_status() -> bool | None:
    raw = await _run_powershell(
        "Get-MpComputerStatus | Select-Object -ExpandProperty RealTimeProtectionEnabled"
    )
    if raw is None or raw == "":
        return None
    return raw.strip().lower() == "true"


async def get_firewall_status() -> bool | None:
    raw = await _run_powershell(
        "(Get-NetFirewallProfile | Where-Object {$_.Enabled -eq $true}).Count"
    )
    if raw is None or raw == "":
        return None
    try:
        return int(raw.strip()) > 0
    except ValueError:
        return None


async def get_update_status() -> dict | None:
    raw = await _run_powershell(
        "(New-Object -ComObject Microsoft.Update.AutoUpdate).Results | ConvertTo-Json"
    )
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    def _parse_dotnet_date(value: str | None) -> str | None:
        if not value:
            return None
        match = _DOTNET_DATE_RE.match(value)
        if not match:
            return None
        from datetime import datetime, timezone

        millis = int(match.group(1))
        return datetime.fromtimestamp(millis / 1000, tz=timezone.utc).isoformat()

    return {
        "last_search": _parse_dotnet_date(data.get("LastSearchSuccessDate")),
        "last_install": _parse_dotnet_date(data.get("LastInstallationSuccessDate")),
    }


async def get_security_snapshot() -> dict:
    defender, firewall, updates = await asyncio.gather(
        get_defender_status(), get_firewall_status(), get_update_status()
    )
    return {"defender_enabled": defender, "firewall_enabled": firewall, "updates": updates}
