import json
import logging
import time
import urllib.error
import urllib.request
import uuid

from agent import utils
from agent.model.base import ModelClient, ModelResponse, ToolCall

log = logging.getLogger("agent")

RETRY_STATUSES = {429, 500, 502, 503, 504}


class LocalOllamaClient(ModelClient):
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        retries: int = 3,
        timeout: float = 300,
    ):
        self.api_key = api_key
        self.model = model
        self.url = base_url.rstrip("/").removesuffix("/v1") + "/api/chat"
        self.retries = retries
        self.timeout = timeout

    def complete(self, messages: list[dict], tools: list[dict]) -> ModelResponse:
        payload: dict = {
            "model": self.model,
            "messages": self._to_ollama_messages(messages),
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
        log.debug(f"payload to send: {utils.truncate_for_log(payload)}")
        data = self._post(payload)
        try:
            log.debug(f"received data: {utils.truncate_for_log(data)}")
            message = data["message"]
        except KeyError:
            raise RuntimeError(f"Unexpected response from Ollama: {data}")
        return ModelResponse(
            content=message.get("content") or "",
            tool_calls=[
                self._parse_tool_call(tc) for tc in message.get("tool_calls") or []
            ],
        )

    @staticmethod
    def _to_ollama_messages(messages: list[dict]) -> list[dict]:
        """OpenAI-style history -> Ollama: tool-call arguments as objects,
        tool results identified by tool_name instead of tool_call_id."""
        names: dict[str, str] = {}
        out = []
        for msg in messages:
            m = dict(msg)
            if calls := msg.get("tool_calls"):
                m["tool_calls"] = []
                for tc in calls:
                    fn = tc["function"]
                    names[tc["id"]] = fn["name"]
                    args = fn.get("arguments") or {}
                    if isinstance(args, str):
                        args = json.loads(args)
                    m["tool_calls"].append(
                        {"function": {"name": fn["name"], "arguments": args}}
                    )
            if name := names.get(msg.get("tool_call_id", "")):
                m["tool_name"] = name
            out.append(m)
        return out

    @staticmethod
    def _parse_tool_call(raw: dict) -> ToolCall:
        # Ollama returns arguments already parsed, and may omit call IDs.
        fn = raw["function"]
        call_id = raw.get("id") or f"call_{uuid.uuid4().hex[:12]}"
        args = fn.get("arguments") or {}
        if not isinstance(args, dict):
            args = {"__parse_error__": "arguments must be a JSON object"}
        return ToolCall(call_id, fn["name"], args)

    def _post(self, payload: dict) -> dict:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            self.url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as e:
                detail = e.read().decode(errors="replace")
                if e.code in RETRY_STATUSES and attempt < self.retries:
                    log.warning(
                        "HTTP %s from model, retrying (%s)", e.code, attempt + 1
                    )
                    time.sleep(2**attempt)
                    continue
                raise RuntimeError(f"Ollama HTTP {e.code}: {detail}") from e
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt < self.retries:
                    log.warning("Network error %s, retrying (%s)", e, attempt + 1)
                    time.sleep(2**attempt)
                    continue
                raise RuntimeError(f"Ollama request failed: {e}") from e
        raise RuntimeError("unreachable")
