from app.ai.conversation import MAX_HISTORY_MESSAGES, ConversationManager


def test_messages_for_request_includes_system_prompt_and_user_text():
    manager = ConversationManager()
    messages = manager.messages_for_request("open chrome")

    assert messages[0]["role"] == "system"
    assert messages[-1] == {"role": "user", "content": "open chrome"}


def test_history_trims_to_max_length():
    manager = ConversationManager()
    for i in range(MAX_HISTORY_MESSAGES + 10):
        manager.messages_for_request(f"message {i}")
        manager.add_assistant_reply(f"reply {i}")

    assert len(manager._history) == MAX_HISTORY_MESSAGES
