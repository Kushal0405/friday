from __future__ import annotations

import asyncio
from typing import Any

from app.ai.pipeline_stats import pipeline_stats
from app.core.logging import get_logger
from app.events.bus import event_bus
from app.system.active_window import get_active_window
from app.system.monitor import get_audio_devices, get_network_throughput_mbps, get_system_stats
from app.system.security import get_security_snapshot
from app.system.weather import get_weather_snapshot

logger = get_logger("system.broadcaster")

SYSTEM_STATS_INTERVAL_SECONDS = 2
ACTIVE_WINDOW_INTERVAL_SECONDS = 1.5
WEATHER_INTERVAL_SECONDS = 600
SECURITY_INTERVAL_SECONDS = 300
PIPELINE_STATS_INTERVAL_SECONDS = 2

# Last known value per event type, so a client that connects between two
# periodic publishes (e.g. right after startup, or between infrequent
# weather/security refreshes) still gets an immediate snapshot instead of
# waiting out the full interval or missing an on-change event entirely.
last_known: dict[str, dict[str, Any]] = {}


async def _system_stats_loop() -> None:
    audio = await asyncio.to_thread(get_audio_devices)
    while True:
        stats = await asyncio.to_thread(get_system_stats)
        network_mbps = await asyncio.to_thread(get_network_throughput_mbps)
        event = {
            "type": "system_stats",
            **stats,
            "network_mbps": network_mbps,
            "microphone": audio["microphone"],
            "speaker": audio["speaker"],
        }
        last_known["system_stats"] = event
        await event_bus.publish(event)
        await asyncio.sleep(SYSTEM_STATS_INTERVAL_SECONDS)


async def _active_window_loop() -> None:
    last: dict | None = None
    while True:
        window = await asyncio.to_thread(get_active_window)
        if window != last:
            last = window
            event = {
                "type": "active_window",
                "app_name": window["app_name"] if window else None,
                "title": window["title"] if window else None,
            }
            last_known["active_window"] = event
            await event_bus.publish(event)
        await asyncio.sleep(ACTIVE_WINDOW_INTERVAL_SECONDS)


async def _weather_loop() -> None:
    while True:
        snapshot = await get_weather_snapshot()
        if snapshot:
            event = {"type": "weather", **snapshot}
            last_known["weather"] = event
            await event_bus.publish(event)
        await asyncio.sleep(WEATHER_INTERVAL_SECONDS)


async def _security_loop() -> None:
    while True:
        snapshot = await get_security_snapshot()
        event = {"type": "security_status", **snapshot}
        last_known["security_status"] = event
        await event_bus.publish(event)
        await asyncio.sleep(SECURITY_INTERVAL_SECONDS)


async def _pipeline_stats_loop() -> None:
    while True:
        stats = pipeline_stats.snapshot()
        event = {"type": "pipeline_stats", **stats.model_dump()}
        last_known["pipeline_stats"] = event
        await event_bus.publish(event)
        await asyncio.sleep(PIPELINE_STATS_INTERVAL_SECONDS)


def start_broadcasters() -> list[asyncio.Task]:
    return [
        asyncio.create_task(_system_stats_loop()),
        asyncio.create_task(_active_window_loop()),
        asyncio.create_task(_weather_loop()),
        asyncio.create_task(_security_loop()),
        asyncio.create_task(_pipeline_stats_loop()),
    ]
