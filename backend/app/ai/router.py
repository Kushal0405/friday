from __future__ import annotations

import json

from app.ai.conversation import conversation_manager
from app.ai.pipeline_stats import Stopwatch, pipeline_stats
from app.ai.provider import AIProviderError, ai_provider
from app.core.config import settings
from app.core.logging import get_logger
from app.events.bus import event_bus
from app.tasks.manager import task_manager
from app.tools.registry import tool_registry

logger = get_logger("router")

TOOL_DISPLAY_NAMES = {
    "get_time": "Checking the time",
    "open_application": "Opening application",
    "close_application": "Closing application",
    "get_system_status": "Reading system status",
    "play_video": "Playing video",
    "delete_file": "Deleting file",
}


class CommandRouter:
    async def handle_text(self, text: str) -> str:
        logger.info("TEXT RECEIVED: %s", text)
        await event_bus.publish({"type": "transcript", "text": text})
        await event_bus.publish({"type": "thinking", "active": True})

        messages = conversation_manager.messages_for_request(text)
        tools = tool_registry.schemas()

        stopwatch = Stopwatch()
        try:
            reply = await ai_provider.chat(messages, tools=tools or None)
        except AIProviderError as exc:
            logger.error("AI UNAVAILABLE: %s", exc)
            pipeline_stats.record_error()
            await event_bus.publish(
                {
                    "type": "error",
                    "message": "AI provider is unavailable. Check that your configured "
                    "backend (e.g. Ollama) is running.",
                    "context": "ai_provider",
                }
            )
            await event_bus.publish({"type": "thinking", "active": False})
            return ""

        provider_name = getattr(ai_provider, "last_winner", None) or type(ai_provider).__name__
        pipeline_stats.record_request(provider_name, stopwatch.elapsed_ms())

        if reply.tool_calls:
            return await self._handle_tool_calls(reply, messages)

        reply_text = reply.content or ""
        conversation_manager.add_assistant_reply(reply_text)
        await event_bus.publish({"type": "thinking", "active": False})
        await event_bus.publish({"type": "assistant_response", "text": reply_text})
        return reply_text

    async def _handle_tool_calls(self, reply, messages: list) -> str:
        messages.append(
            {
                "role": "assistant",
                "content": reply.content or "",
                "tool_calls": [tc.model_dump() for tc in reply.tool_calls],
            }
        )

        for tool_call in reply.tool_calls:
            tool_name = tool_call.function.name
            tool = tool_registry.get(tool_name)
            pipeline_stats.record_tool_call()

            display_name = TOOL_DISPLAY_NAMES.get(tool_name, tool_name)
            task = await task_manager.start(display_name)
            await event_bus.publish({"type": "tool_started", "tool": tool_name, "task_id": task.id})

            if not tool:
                result_text = f"Unknown tool: {tool_name}"
                await task_manager.fail(task.id, result_text)
                await event_bus.publish(
                    {"type": "tool_completed", "tool": tool_name, "task_id": task.id, "success": False}
                )
            else:
                try:
                    raw_args = json.loads(tool_call.function.arguments or "{}")
                    params = tool.parameters(**raw_args)
                    result = await tool.execute(params)
                except Exception as exc:  # noqa: BLE001 - convert any tool failure into a result
                    logger.error("TOOL %s FAILED: %s", tool_name, exc)
                    result_text = f"Tool failed: {exc}"
                    await task_manager.fail(task.id, result_text)
                    await event_bus.publish(
                        {"type": "tool_completed", "tool": tool_name, "task_id": task.id, "success": False}
                    )
                else:
                    result_text = result.message
                    if result.success:
                        await task_manager.complete(task.id, result_text)
                    else:
                        await task_manager.fail(task.id, result_text)
                    await event_bus.publish(
                        {
                            "type": "tool_completed",
                            "tool": tool_name,
                            "task_id": task.id,
                            "success": result.success,
                        }
                    )

            messages.append(
                {"role": "tool", "tool_call_id": tool_call.id, "content": result_text}
            )

        try:
            final_reply = await ai_provider.chat(messages)
            final_text = final_reply.content or ""
        except AIProviderError:
            final_text = "Done."

        conversation_manager.add_assistant_reply(final_text)
        await event_bus.publish({"type": "thinking", "active": False})
        await event_bus.publish({"type": "assistant_response", "text": final_text})
        return final_text


command_router = CommandRouter()
