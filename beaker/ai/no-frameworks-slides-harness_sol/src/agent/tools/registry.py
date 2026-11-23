import json
import logging
from collections.abc import Callable
from dataclasses import dataclass

log = logging.getLogger("agent")


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict  # JSON schema for the arguments object
    fn: Callable[..., str]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def tool(self, name: str, description: str, parameters: dict) -> Callable:
        """Decorator: register a function as a tool with a hand-written JSON schema."""

        def decorator(fn: Callable[..., str]) -> Callable[..., str]:
            if name in self._tools:
                raise ValueError(f"duplicate tool: {name}")
            self._tools[name] = Tool(name, description, parameters, fn)
            return fn

        return decorator

    def schemas(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self._tools.values()
        ]

    def execute(self, name: str, arguments: dict) -> str:
        """Run a tool. Errors are returned as text so the model can recover."""
        tool = self._tools.get(name)
        if tool is None:
            return f"Error: unknown tool '{name}'. Available: {', '.join(self._tools)}"
        if "__parse_error__" in arguments:
            return f"Error: {arguments['__parse_error__']}"
        try:
            result = tool.fn(**arguments)
        except TypeError as e:
            return f"Error: bad arguments for '{name}': {e}"
        except Exception as e:  # tool failures are data for the model, not crashes
            log.debug("tool %s failed", name, exc_info=True)
            return f"Error: {type(e).__name__}: {e}"
        return result if isinstance(result, str) else json.dumps(result)
