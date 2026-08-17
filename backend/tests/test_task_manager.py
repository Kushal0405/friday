from app.events.bus import event_bus
from app.tasks.manager import TaskManager


async def test_start_publishes_task_started_and_sets_running():
    manager = TaskManager()
    queue = event_bus.subscribe()
    try:
        task = await manager.start("Opening application")
        event = await queue.get()

        assert event["type"] == "task_started"
        assert event["task"]["status"] == "RUNNING"
        assert task.status == "RUNNING"
    finally:
        event_bus.unsubscribe(queue)


async def test_complete_sets_completed_status_with_result():
    manager = TaskManager()
    queue = event_bus.subscribe()
    try:
        task = await manager.start("Checking time")
        await queue.get()
        await manager.complete(task.id, "It is noon.")
        event = await queue.get()

        assert event["type"] == "task_completed"
        assert event["task"]["status"] == "COMPLETED"
        assert event["task"]["result"] == "It is noon."
    finally:
        event_bus.unsubscribe(queue)


async def test_fail_sets_failed_status_with_error():
    manager = TaskManager()
    queue = event_bus.subscribe()
    try:
        task = await manager.start("Opening application")
        await queue.get()
        await manager.fail(task.id, "App not found")
        event = await queue.get()

        assert event["type"] == "task_completed"
        assert event["task"]["status"] == "FAILED"
        assert event["task"]["error"] == "App not found"
    finally:
        event_bus.unsubscribe(queue)
