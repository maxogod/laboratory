import json
import re
import tomllib
from pathlib import Path

import pytest

from mcp_server.main import mcp

PROJECT_DIR = Path(__file__).parent.parent
POLICY_FILE = PROJECT_DIR / "policies" / "atlassian-mcp.toml"
ANTIGRAVITY_FILE = PROJECT_DIR / "policies" / "antigravity.json"
GEMINI_ALWAYS_ALLOW_PRIORITY = 950


def _rules() -> list[dict]:
    return tomllib.loads(POLICY_FILE.read_text(encoding="utf-8"))["rule"]


def _server_rule_with_decision(decision: str) -> dict:
    return next(
        rule
        for rule in _rules()
        if rule.get("mcpName") == "atlassian-mcp" and rule["decision"] == decision
    )


def _skill_rule() -> dict:
    return next(rule for rule in _rules() if rule["toolName"] == "activate_skill")


@pytest.mark.asyncio
async def test_policy_allows_exactly_the_read_only_tools():
    tools = await mcp.list_tools()
    read_only_tools = {tool.name for tool in tools if tool.annotations.read_only_hint}
    assert set(_server_rule_with_decision("allow")["toolName"]) == read_only_tools


@pytest.mark.asyncio
async def test_every_tool_declares_whether_it_writes():
    for tool in await mcp.list_tools():
        assert tool.annotations.read_only_hint is not None, tool.name


@pytest.mark.asyncio
async def test_edit_tools_are_marked_destructive():
    destructive_tools = {
        tool.name
        for tool in await mcp.list_tools()
        if tool.annotations.destructive_hint
    }
    assert destructive_tools == {"bitbucket_edit_pr", "jira_edit_ticket"}


def test_tools_not_explicitly_allowed_ask_for_approval():
    fallback = _server_rule_with_decision("ask_user")
    assert fallback["mcpName"] == "atlassian-mcp"
    assert fallback["toolName"] == "*"


def test_every_rule_names_its_tools():
    assert all("toolName" in rule for rule in _rules())


def test_policy_outranks_saved_always_allow_approvals():
    allow = _server_rule_with_decision("allow")
    ask_user = _server_rule_with_decision("ask_user")
    assert allow["priority"] > ask_user["priority"] > GEMINI_ALWAYS_ALLOW_PRIORITY


def test_use_guide_skill_loads_without_approval():
    rule = _skill_rule()
    assert rule["decision"] == "allow"
    assert re.search(rule["argsPattern"], '{"name":"attlassian-mcp-use-guide"}')
    assert (PROJECT_DIR / "skills" / "attlassian-mcp-use-guide" / "SKILL.md").is_file()


@pytest.mark.parametrize(
    "skill", ["other-skill", "attlassian-mcp-use-guide-2", "x-attlassian-mcp-use-guide"]
)
def test_other_skills_still_need_approval(skill):
    assert not re.search(_skill_rule()["argsPattern"], f'{{"name":"{skill}"}}')


def _antigravity_tools(decision: str) -> set[str]:
    permissions = json.loads(ANTIGRAVITY_FILE.read_text(encoding="utf-8"))[
        "permissions"
    ]
    return {
        match.group(1)
        for rule in permissions[decision]
        if (match := re.fullmatch(r"mcp\(atlassian-mcp/(.+)\)", rule))
    }


@pytest.mark.asyncio
async def test_antigravity_allows_reads_and_asks_for_every_write():
    tools = await mcp.list_tools()
    reads = {tool.name for tool in tools if tool.annotations.read_only_hint}
    writes = {tool.name for tool in tools} - reads
    assert _antigravity_tools("allow") == reads
    assert _antigravity_tools("ask") == writes
