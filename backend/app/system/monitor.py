from __future__ import annotations

import platform
import time

import psutil
import sounddevice as sd

_last_net_sample: tuple[float, int, int] | None = None


def get_system_stats() -> dict:
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("C:\\").percent

    battery = psutil.sensors_battery()
    battery_pct = battery.percent if battery else None

    uptime_seconds = time.time() - psutil.boot_time()

    return {
        "cpu": cpu,
        "ram": ram,
        "disk": disk,
        "battery": battery_pct,
        "os": f"{platform.system()} {platform.release()}",
        "uptime_seconds": int(uptime_seconds),
    }


def get_network_throughput_mbps() -> float:
    """Computes real throughput from the delta between successive polls.
    Returns 0.0 on the very first call (no prior sample to diff against)."""
    global _last_net_sample
    counters = psutil.net_io_counters()
    now = time.monotonic()
    total_bytes = counters.bytes_sent + counters.bytes_recv

    if _last_net_sample is None:
        _last_net_sample = (now, total_bytes, total_bytes)
        return 0.0

    last_time, _, last_total = _last_net_sample
    elapsed = now - last_time
    _last_net_sample = (now, total_bytes, total_bytes)

    if elapsed <= 0:
        return 0.0
    bytes_per_sec = (total_bytes - last_total) / elapsed
    return round((bytes_per_sec * 8) / 1_000_000, 1)  # Mbps


def get_audio_devices() -> dict:
    try:
        devices = sd.query_devices()
        default_in, default_out = sd.default.device
        input_name = devices[default_in]["name"] if default_in is not None and default_in >= 0 else None
        output_name = devices[default_out]["name"] if default_out is not None and default_out >= 0 else None
        return {"microphone": input_name, "speaker": output_name}
    except Exception:  # noqa: BLE001 - audio backend can fail in odd environments
        return {"microphone": None, "speaker": None}
