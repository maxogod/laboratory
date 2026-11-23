import json
from pathlib import Path

from agent.model.base import ModelResponse


class Context:
    """Conversation state: the OpenAI-style message list sent to the model each turn.

    Every change is written to `path` as JSON so a session can be resumed later.
    """

    def __init__(self, messages: list[dict], path: Path) -> None:
        self.messages = messages
        self.path = path

    @classmethod
    def new(cls, system_prompt: str, path: Path) -> Context:
        ctx = cls([{"role": "system", "content": system_prompt}], path)
        ctx._save()
        return ctx

    @classmethod
    def load(cls, path: Path) -> Context:
        return cls(json.loads(path.read_text()), path)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.messages, indent=2))

    def add_user(self, text: str) -> None:
        self.messages.append({"role": "user", "content": text})
        self._save()

    def add_assistant(self, response: ModelResponse) -> None:
        msg: dict = {"role": "assistant", "content": response.content or None}
        if response.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments),
                    },
                }
                for tc in response.tool_calls
            ]
        self.messages.append(msg)
        self._save()

    def add_tool_result(self, tool_call_id: str, content: str) -> None:
        self.messages.append(
            {"role": "tool", "tool_call_id": tool_call_id, "content": content}
        )
        self._save()
