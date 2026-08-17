from app.tools.active_window_tool import ActiveWindowTool
from app.tools.application_tool import CloseApplicationTool, OpenApplicationTool
from app.tools.file_tool import DeleteFileTool
from app.tools.media_tool import PlayVideoTool
from app.tools.registry import tool_registry
from app.tools.system_tool import SystemStatusTool
from app.tools.time_tool import TimeTool


def register_all_tools() -> None:
    tool_registry.register(TimeTool())
    tool_registry.register(OpenApplicationTool())
    tool_registry.register(CloseApplicationTool())
    tool_registry.register(SystemStatusTool())
    tool_registry.register(ActiveWindowTool())
    tool_registry.register(PlayVideoTool())
    tool_registry.register(DeleteFileTool())
