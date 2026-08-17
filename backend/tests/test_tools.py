from pydantic import BaseModel

from app.tools.base import Tool, ToolResult
from app.tools.registry import ToolRegistry


class _NoopParams(BaseModel):
    pass


class _NoopTool(Tool):
    name = "noop"
    description = "Does nothing, used for registry tests."
    parameters = _NoopParams

    async def execute(self, params: BaseModel) -> ToolResult:
        return ToolResult(success=True, message="done")


def test_registry_register_and_get():
    registry = ToolRegistry()
    tool = _NoopTool()
    registry.register(tool)

    assert registry.get("noop") is tool
    assert registry.get("missing") is None
    assert registry.list() == [tool]


def test_registry_schemas_are_openai_tool_format():
    registry = ToolRegistry()
    registry.register(_NoopTool())

    schemas = registry.schemas()
    assert schemas[0]["type"] == "function"
    assert schemas[0]["function"]["name"] == "noop"
    assert "parameters" in schemas[0]["function"]


async def test_noop_tool_executes():
    result = await _NoopTool().execute(_NoopParams())
    assert result.success is True
    assert result.message == "done"
