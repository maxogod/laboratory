import json
import stat
from pathlib import Path

import pytest


@pytest.fixture
def setup_antigravity(load_script):
    return load_script("setup_antigravity")


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _mcp_config(home: Path) -> Path:
    return home / ".gemini" / "config" / "mcp_config.json"


def _cli_settings(home: Path) -> Path:
    return home / ".gemini" / "antigravity-cli" / "settings.json"


def test_installs_server_permissions_and_skill(setup_antigravity, tmp_path, capsys):
    setup_antigravity.main()

    server = _read(_mcp_config(tmp_path))["mcpServers"]["atlassian-mcp"]
    assert server["command"] == "uv"
    assert server["args"][-2:] == ["run", "atlassian-mcp"]

    permissions = _read(_cli_settings(tmp_path))["permissions"]
    assert "mcp(atlassian-mcp/jira_read_ticket)" in permissions["allow"]
    assert "mcp(atlassian-mcp/jira_edit_ticket)" in permissions["ask"]

    skill = "attlassian-mcp-use-guide"
    assert (tmp_path / ".gemini" / "config" / "skills" / skill / "SKILL.md").is_file()


def test_prints_the_rules_the_app_needs(setup_antigravity, capsys):
    setup_antigravity.main()
    output = capsys.readouterr().out
    assert "mcp(atlassian-mcp/jira_read_ticket)" in output
    assert "mcp(atlassian-mcp/jira_edit_ticket)" in output


def test_cli_settings_are_private(setup_antigravity, tmp_path):
    setup_antigravity.main()
    assert stat.S_IMODE(_cli_settings(tmp_path).stat().st_mode) == 0o600


def test_keeps_existing_config(setup_antigravity, tmp_path):
    _write(_mcp_config(tmp_path), {"mcpServers": {"other": {"command": "x"}}})
    _write(
        _cli_settings(tmp_path),
        {
            "model": "custom",
            "permissions": {
                "allow": ["command(git)"],
                "ask": ["command(*)"],
                "deny": ["mcp(atlassian-mcp/jira_create_ticket)"],
            },
        },
    )

    setup_antigravity.main()

    assert _read(_mcp_config(tmp_path))["mcpServers"]["other"] == {"command": "x"}
    settings = _read(_cli_settings(tmp_path))
    assert settings["model"] == "custom"
    assert "command(git)" in settings["permissions"]["allow"]
    assert "command(*)" in settings["permissions"]["ask"]
    assert settings["permissions"]["deny"] == ["mcp(atlassian-mcp/jira_create_ticket)"]


def test_replaces_earlier_rules_for_this_server(setup_antigravity, tmp_path):
    _write(
        _cli_settings(tmp_path),
        {
            "permissions": {
                "allow": ["mcp(atlassian-mcp/jira_edit_ticket)"],
                "ask": ["mcp(atlassian-mcp/*)"],
            }
        },
    )

    setup_antigravity.main()

    permissions = _read(_cli_settings(tmp_path))["permissions"]
    assert "mcp(atlassian-mcp/jira_edit_ticket)" not in permissions["allow"]
    assert "mcp(atlassian-mcp/*)" not in permissions["ask"]


def test_can_run_repeatedly(setup_antigravity, tmp_path):
    setup_antigravity.main()
    first = _read(_cli_settings(tmp_path))
    setup_antigravity.main()
    assert _read(_cli_settings(tmp_path)) == first


def test_does_not_change_anything_if_a_file_is_unparseable(setup_antigravity, tmp_path):
    settings_file = _cli_settings(tmp_path)
    settings_file.parent.mkdir(parents=True)
    settings_file.write_text("// a comment", encoding="utf-8")

    with pytest.raises(SystemExit, match="Nothing was changed"):
        setup_antigravity.main()

    assert settings_file.read_text(encoding="utf-8") == "// a comment"
    assert not _mcp_config(tmp_path).exists()
