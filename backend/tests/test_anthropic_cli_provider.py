import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.anthropic_cli_provider import AnthropicCLIProvider
from app.ai.provider import AIProviderError


def test_render_prompt_includes_system_and_formats_turns():
    # The system prompt must be carried through — without it the CLI has no
    # idea it's FRIDAY with real OS tools and defaults to refusing requests
    # its MCP tools could actually perform.
    messages = [
        {"role": "system", "content": "You are FRIDAY."},
        {"role": "user", "content": "open chrome"},
        {"role": "assistant", "content": "Opening Chrome."},
    ]
    prompt = AnthropicCLIProvider._render_prompt(messages)
    assert "You are FRIDAY." in prompt
    assert "User: open chrome" in prompt
    assert "FRIDAY: Opening Chrome." in prompt


@pytest.mark.asyncio
async def test_chat_returns_result_text_with_no_tool_calls():
    provider = AnthropicCLIProvider.__new__(AnthropicCLIProvider)
    provider._config_path = "dummy.json"

    fake_payload = json.dumps({"is_error": False, "result": "It is noon."}).encode()
    fake_proc = MagicMock()
    fake_proc.communicate = AsyncMock(return_value=(fake_payload, b""))
    fake_proc.returncode = 0

    with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=fake_proc)):
        reply = await provider.chat([{"role": "user", "content": "what time is it?"}])

    assert reply.content == "It is noon."
    assert reply.tool_calls is None


@pytest.mark.asyncio
async def test_chat_raises_on_cli_error_payload():
    provider = AnthropicCLIProvider.__new__(AnthropicCLIProvider)
    provider._config_path = "dummy.json"

    fake_payload = json.dumps({"is_error": True, "result": "boom"}).encode()
    fake_proc = MagicMock()
    fake_proc.communicate = AsyncMock(return_value=(fake_payload, b""))
    fake_proc.returncode = 0

    with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=fake_proc)):
        with pytest.raises(AIProviderError):
            await provider.chat([{"role": "user", "content": "x"}])


@pytest.mark.asyncio
async def test_chat_raises_on_nonzero_exit_code():
    provider = AnthropicCLIProvider.__new__(AnthropicCLIProvider)
    provider._config_path = "dummy.json"

    fake_proc = MagicMock()
    fake_proc.communicate = AsyncMock(return_value=(b"", b"claude: command not found"))
    fake_proc.returncode = 127

    with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=fake_proc)):
        with pytest.raises(AIProviderError):
            await provider.chat([{"role": "user", "content": "x"}])
