import json
import logging
import time
import urllib.error
import urllib.request

from agent import utils
from agent.model.base import ModelClient, ModelResponse, ToolCall

log = logging.getLogger("agent")

RETRY_STATUSES = {429, 500, 502, 503, 504}


class OpenRouterClient(ModelClient):
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        retries: int = 3,
        timeout: float = 120,
    ):
        self.api_key = api_key
        self.model = model
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.retries = retries
        self.timeout = timeout

    def complete(self, messages: list[dict], tools: list[dict]) -> ModelResponse:
        payload: dict = {"model": self.model, "messages": messages}
        if tools:
            payload["tools"] = tools
        log.debug(f"payload to send: {utils.truncate_for_log(payload)}")
        data = self._post(payload)
        try:
            log.debug(f"received data: {utils.truncate_for_log(data)}")
            message = data["choices"][0]["message"]
        except KeyError, IndexError:
            raise RuntimeError(f"Unexpected response from OpenRouter: {data}")
        return ModelResponse(
            content=message.get("content") or "",
            tool_calls=[
                self._parse_tool_call(tc) for tc in message.get("tool_calls") or []
            ],
        )

    @staticmethod
    def _parse_tool_call(raw: dict) -> ToolCall:
        fn = raw["function"]
        try:
            args = json.loads(fn.get("arguments") or "{}")
            if not isinstance(args, dict):
                raise TypeError("arguments must be a JSON object")
        except TypeError as e:
            return ToolCall(
                raw["id"],
                fn["name"],
                {"__parse_error__": f"invalid arguments JSON: {e}"},
            )
        return ToolCall(raw["id"], fn["name"], args)

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
                raise RuntimeError(f"OpenRouter HTTP {e.code}: {detail}") from e
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt < self.retries:
                    log.warning("Network error %s, retrying (%s)", e, attempt + 1)
                    time.sleep(2**attempt)
                    continue
                raise RuntimeError(f"OpenRouter request failed: {e}") from e
        raise RuntimeError("unreachable")
