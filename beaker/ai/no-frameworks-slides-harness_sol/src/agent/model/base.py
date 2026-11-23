from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass(frozen=True)
class ModelResponse:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)


class ModelClient(ABC):
    @abstractmethod
    def complete(self, messages: list[dict], tools: list[dict]) -> ModelResponse:
        """Send chat messages + tool schemas, return text and structured tool calls."""
