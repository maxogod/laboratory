import urllib.request
from html.parser import HTMLParser

from agent.tools.registry import ToolRegistry

MAX_CHARS = 20_000
SKIP_TAGS = {"script", "style", "noscript", "head", "svg"}
BLOCK_TAGS = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self._skip += 1
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    lines = (" ".join(line.split()) for line in "".join(parser.parts).splitlines())
    return "\n".join(line for line in lines if line)


def register(registry: ToolRegistry) -> None:
    @registry.tool(
        name="fetch_url",
        description="Fetch a web page over HTTP(S) and return its readable text content (truncated).",
        parameters={
            "type": "object",
            "properties": {"url": {"type": "string", "description": "http(s) URL to fetch"}},
            "required": ["url"],
        },
    )
    def fetch_url(url: str) -> str:
        if not url.startswith(("http://", "https://")):
            raise ValueError("only http(s) URLs are allowed")
        req = urllib.request.Request(url, headers={"User-Agent": "agent/0.1"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read(2_000_000).decode(resp.headers.get_content_charset() or "utf-8", errors="replace")
            is_html = "html" in resp.headers.get_content_type()
        text = html_to_text(raw) if is_html else raw
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + f"\n...[truncated, {len(text)} chars total]"
        return text
