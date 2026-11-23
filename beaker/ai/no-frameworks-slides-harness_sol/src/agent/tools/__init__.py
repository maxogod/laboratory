from pathlib import Path

from agent.tools import html_file_operations, web
from agent.tools.registry import ToolRegistry


def build_registry(workspace: Path) -> ToolRegistry:
    registry = ToolRegistry()
    web.register(registry)
    html_file_operations.register(registry, workspace)
    return registry
