"""AI provider that shells out to the already-installed Claude Code CLI,
using the user's Claude subscription instead of a separately billed
Anthropic API key.

Unlike OpenAICompatibleProvider, the CLI is a self-contained agent: it
decides on its own whether to call a FRIDAY tool (exposed over a local MCP
server, see app/ai/mcp_server.py) and returns a final natural-language
answer in one shot. So chat() here always returns a message with
tool_calls=None — CommandRouter's tool-execution branch is a no-op for this
provider, since execution already happened inside the CLI subprocess.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from app.ai.base_provider import AIProvider, AIProviderError
from app.core.config import settings
from app.core.logging import get_logger
from app.tools.registry import tool_registry

logger = get_logger("ai.anthropic_cli")

MCP_SERVER_MODULE = "app.ai.mcp_server"
DISALLOWED_BUILTIN_TOOLS = (
    "Bash PowerShell Edit Write Read Glob Grep WebFetch WebSearch "
    "Task NotebookEdit Artifact ScheduleWakeup"
)
CLI_TIMEOUT_SECONDS = 90


def _backend_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _mcp_config_path() -> Path:
    """A stable MCP config file (not regenerated per-call) pointing the CLI
    subprocess at FRIDAY's tool server, using this same venv's interpreter."""
    config = {
        "mcpServers": {
            "friday-tools": {
                "command": str(Path(os.sys.executable).as_posix()),
                "args": ["-m", MCP_SERVER_MODULE],
                "cwd": str(_backend_dir().as_posix()),
            }
        }
    }
    path = Path(tempfile.gettempdir()) / "friday-mcp-config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def _allowed_tool_names() -> list[str]:
    return [f"mcp__friday-tools__{tool.name}" for tool in tool_registry.list()]


def _resolve_claude_executable() -> str:
    """On Windows, the `claude` on PATH is a .cmd shim that
    asyncio.create_subprocess_exec cannot launch directly (CreateProcess has
    no shell association for .cmd/.bat). The shim's only job is to forward to
    a real native claude.exe sitting next to it in
    node_modules/@anthropic-ai/claude-code/bin/ — resolve and call that
    directly instead of going through cmd.exe."""
    cmd_path = shutil.which("claude.cmd") or shutil.which("claude.exe")
    if cmd_path and cmd_path.lower().endswith(".exe"):
        return cmd_path
    if cmd_path:
        real_exe = Path(cmd_path).parent / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
        if real_exe.exists():
            return str(real_exe)

    plain = shutil.which("claude")
    if plain:
        return plain

    raise AIProviderError("Claude CLI not found on PATH. Install Claude Code and ensure `claude` is available.")


class AnthropicCLIProvider(AIProvider):
    def __init__(self) -> None:
        self._config_path = _mcp_config_path()

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> Any:
        prompt = self._render_prompt(messages)
        allowed = _allowed_tool_names()

        env = os.environ.copy()
        env.pop("ELECTRON_RUN_AS_NODE", None)

        cmd = [
            _resolve_claude_executable(),
            "-p",
            prompt,
            "--mcp-config",
            str(self._config_path),
            "--strict-mcp-config",
            "--allowedTools",
            *allowed,
            "--disallowedTools",
            *DISALLOWED_BUILTIN_TOOLS.split(),
            "--model",
            settings.anthropic_cli_model,
            "--output-format",
            "json",
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=CLI_TIMEOUT_SECONDS
            )
        except asyncio.CancelledError:
            # e.g. RaceProvider cancelled us after another provider answered
            # first — kill the CLI subprocess rather than leaving an orphan.
            proc.kill()
            raise
        except (asyncio.TimeoutError, OSError) as exc:
            proc.kill()
            logger.error("CLAUDE CLI ERROR: %s", exc)
            raise AIProviderError(f"Claude CLI unavailable: {exc}") from exc

        if proc.returncode != 0:
            logger.error("CLAUDE CLI EXIT %s: %s", proc.returncode, stderr.decode(errors="ignore"))
            raise AIProviderError(f"Claude CLI exited with code {proc.returncode}")

        try:
            payload = json.loads(stdout.decode(errors="ignore"))
        except json.JSONDecodeError as exc:
            raise AIProviderError(f"Claude CLI returned invalid JSON: {exc}") from exc

        if payload.get("is_error"):
            raise AIProviderError(payload.get("result", "Claude CLI reported an error"))

        text = payload.get("result", "")
        return SimpleNamespace(content=text, tool_calls=None)

    @staticmethod
    def _render_prompt(messages: list[dict[str, Any]]) -> str:
        """Collapse FRIDAY's chat history into a single prompt string, since
        the CLI's -p mode takes one prompt per invocation (each call is a
        fresh subprocess/session, not a persisted multi-turn conversation).

        The system message is carried through (not dropped) — without it the
        CLI has no idea it's FRIDAY with real OS tools available and defaults
        to its own "I'm just a coding assistant" persona, refusing requests
        its MCP tools can actually perform."""
        lines = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content") or ""
            if role == "system":
                lines.append(str(content))
            elif role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"FRIDAY: {content}")
        return "\n".join(lines)
