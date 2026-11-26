import re
from itertools import groupby
from typing import Any

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
BULLET_ITEM = re.compile(r"^\s*[-*+]\s+(.*)$")
ORDERED_ITEM = re.compile(r"^\s*\d+\.\s+(.*)$")
RULE = re.compile(r"^-{3,}\s*$")
CODE_FENCE = re.compile(r"^```(\w*)\n(.*?)^```\s*$", re.DOTALL | re.MULTILINE)
INLINE_MARK = re.compile(
    r"\*\*(?P<strong>.+?)\*\*"
    r"|\*(?P<em>\S(?:.*?\S)?)\*"
    r"|`(?P<code>.+?)`"
    r"|\[(?P<label>.+?)\]\((?P<href>[^)\s]+)\)"
)


def parse_adf_to_text(adf: Any | None) -> str:
    """Recursively parse Atlassian Document Format (ADF) to plain text / Markdown."""
    if not adf:
        return ""

    if isinstance(adf, list):
        return "".join(parse_adf_to_text(item) for item in adf)

    if not isinstance(adf, dict):
        return str(adf)

    node_type = adf.get("type")

    if node_type == "text":
        return adf.get("text", "")

    if node_type == "hardBreak":
        return "\n"

    content = adf.get("content")
    if content:
        text_parts = []
        for item in content:
            text_parts.append(parse_adf_to_text(item))

        joined = "".join(text_parts)
        if node_type in ("paragraph", "heading"):
            return joined.rstrip("\n") + "\n"
        elif node_type == "listItem":
            return "* " + joined.lstrip("* ").rstrip("\n") + "\n"
        elif node_type in ("bulletList", "orderedList"):
            return joined
        return joined

    return ""


def markdown_to_adf(markdown: str) -> dict[str, Any]:
    """Convert Markdown to an ADF document, which Jira REST API v3 requires.

    Supports headings, flat lists, fenced code, rules, bold, italic, inline code
    and links. Anything else is kept as literal text.
    """
    # re.split with two capture groups yields [text, language, code, text, ...]
    parts = CODE_FENCE.split(markdown)
    content: list[dict[str, Any]] = _text_blocks(parts[0])
    for index in range(1, len(parts), 3):
        language, code, following_text = parts[index : index + 3]
        content.append(_code_block(code, language))
        content.extend(_text_blocks(following_text))
    return {"type": "doc", "version": 1, "content": content}


def _text_blocks(text: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for kind, group in groupby(text.splitlines(), _line_kind):
        lines = list(group)
        if kind == "heading":
            blocks.extend(_heading(line) for line in lines)
        elif kind == "rule":
            blocks.extend({"type": "rule"} for _ in lines)
        elif kind == "bulletList":
            blocks.append(_list(kind, lines, BULLET_ITEM))
        elif kind == "orderedList":
            blocks.append(_list(kind, lines, ORDERED_ITEM))
        elif kind == "paragraph":
            blocks.append(_paragraph(lines))
    return blocks


def _line_kind(line: str) -> str:
    if not line.strip():
        return "blank"
    if HEADING.match(line):
        return "heading"
    if RULE.match(line):
        return "rule"
    if BULLET_ITEM.match(line):
        return "bulletList"
    if ORDERED_ITEM.match(line):
        return "orderedList"
    return "paragraph"


def _heading(line: str) -> dict[str, Any]:
    hashes, text = HEADING.match(line).groups()  # type: ignore[union-attr]
    return {
        "type": "heading",
        "attrs": {"level": len(hashes)},
        "content": _inline_nodes(text),
    }


def _list(kind: str, lines: list[str], item_pattern: re.Pattern[str]) -> dict[str, Any]:
    items = [item_pattern.match(line).group(1) for line in lines]  # type: ignore[union-attr]
    return {
        "type": kind,
        "content": [
            {"type": "listItem", "content": [_paragraph([item])]} for item in items
        ],
    }


def _paragraph(lines: list[str]) -> dict[str, Any]:
    content: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        if index > 0:
            content.append({"type": "hardBreak"})
        content.extend(_inline_nodes(line))
    return {"type": "paragraph", "content": content}


def _code_block(code: str, language: str) -> dict[str, Any]:
    code = code.rstrip("\n")
    block: dict[str, Any] = {
        "type": "codeBlock",
        "content": [{"type": "text", "text": code}] if code else [],
    }
    if language:
        block["attrs"] = {"language": language}
    return block


def _inline_nodes(text: str) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    position = 0
    for match in INLINE_MARK.finditer(text):
        if match.start() > position:
            nodes.append({"type": "text", "text": text[position : match.start()]})
        nodes.append(_marked_text(match))
        position = match.end()
    if position < len(text):
        nodes.append({"type": "text", "text": text[position:]})
    return nodes


def _marked_text(match: re.Match[str]) -> dict[str, Any]:
    if match["href"]:
        mark = {"type": "link", "attrs": {"href": match["href"]}}
        return {"type": "text", "text": match["label"], "marks": [mark]}
    kind = match.lastgroup
    assert kind is not None
    return {"type": "text", "text": match[kind], "marks": [{"type": kind}]}
