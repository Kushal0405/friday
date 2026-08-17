from __future__ import annotations

import time

from pydantic import BaseModel


class PipelineStats(BaseModel):
    last_provider: str | None = None
    last_latency_ms: int | None = None
    requests_handled: int = 0
    tool_calls_made: int = 0
    errors: int = 0


class PipelineStatsTracker:
    def __init__(self) -> None:
        self._stats = PipelineStats()

    def record_request(self, provider: str, latency_ms: int) -> None:
        self._stats.last_provider = provider
        self._stats.last_latency_ms = latency_ms
        self._stats.requests_handled += 1

    def record_tool_call(self) -> None:
        self._stats.tool_calls_made += 1

    def record_error(self) -> None:
        self._stats.errors += 1

    def snapshot(self) -> PipelineStats:
        return self._stats.model_copy()


pipeline_stats = PipelineStatsTracker()


class Stopwatch:
    def __init__(self) -> None:
        self._start = time.monotonic()

    def elapsed_ms(self) -> int:
        return int((time.monotonic() - self._start) * 1000)
