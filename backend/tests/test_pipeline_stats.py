from app.ai.pipeline_stats import PipelineStatsTracker


def test_record_request_updates_provider_and_latency():
    tracker = PipelineStatsTracker()
    tracker.record_request("OllamaProvider", 120)

    snap = tracker.snapshot()
    assert snap.last_provider == "OllamaProvider"
    assert snap.last_latency_ms == 120
    assert snap.requests_handled == 1


def test_record_tool_call_increments_counter():
    tracker = PipelineStatsTracker()
    tracker.record_tool_call()
    tracker.record_tool_call()

    assert tracker.snapshot().tool_calls_made == 2


def test_record_error_increments_counter():
    tracker = PipelineStatsTracker()
    tracker.record_error()

    assert tracker.snapshot().errors == 1


def test_snapshot_is_a_copy_not_live_reference():
    tracker = PipelineStatsTracker()
    snap1 = tracker.snapshot()
    tracker.record_tool_call()

    assert snap1.tool_calls_made == 0
