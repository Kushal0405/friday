from __future__ import annotations

from openai.types.chat import ChatCompletionMessageParam

SYSTEM_PROMPT = (
    "You are FRIDAY, a concise voice-first desktop assistant running on the "
    "user's own Windows PC, with real tools that open apps, play media, "
    "manage files, and read system state on this machine. Keep spoken "
    "responses short and natural — a sentence or two, not a list. When a "
    "request requires taking an action on the computer, call the matching "
    "tool immediately instead of describing what you would do or claiming "
    "you can't — if a suitable tool is available, use it rather than "
    "refusing."
)

MAX_HISTORY_MESSAGES = 20


class ConversationManager:
    """Holds a rolling message history for a single session."""

    def __init__(self) -> None:
        self._history: list[ChatCompletionMessageParam] = []

    def messages_for_request(self, user_text: str) -> list[ChatCompletionMessageParam]:
        self._history.append({"role": "user", "content": user_text})
        self._trim()
        return [{"role": "system", "content": SYSTEM_PROMPT}, *self._history]

    def add_assistant_reply(self, text: str) -> None:
        self._history.append({"role": "assistant", "content": text})
        self._trim()

    def _trim(self) -> None:
        if len(self._history) > MAX_HISTORY_MESSAGES:
            self._history = self._history[-MAX_HISTORY_MESSAGES:]

    def reset(self) -> None:
        self._history.clear()


conversation_manager = ConversationManager()
