import json
from pathlib import Path

import pytest


@pytest.fixture
def setup_gemini(load_script):
    return load_script("setup_gemini")


def _read_settings(gemini_dir: Path) -> dict:
    return json.loads((gemini_dir / "settings.json").read_text(encoding="utf-8"))


def test_installs_server_policy_and_skill(setup_gemini, tmp_path):
    setup_gemini.main()

    gemini_dir = tmp_path / ".gemini"
    server = _read_settings(gemini_dir)["mcpServers"]["atlassian-mcp"]
    assert server["command"] == "uv"
    assert server["args"][-2:] == ["run", "atlassian-mcp"]
    assert (gemini_dir / "policies" / "atlassian-mcp.toml").is_file()
    assert (gemini_dir / "skills" / "attlassian-mcp-use-guide" / "SKILL.md").is_file()


def test_keeps_existing_settings_and_removes_trust(setup_gemini, tmp_path):
    gemini_dir = tmp_path / ".gemini"
    gemini_dir.mkdir()
    (gemini_dir / "settings.json").write_text(
        json.dumps(
            {
                "theme": "dark",
                "mcpServers": {"other": {"command": "x"}, "atlassian-mcp": {"trust": True}},
            }
        ),
        encoding="utf-8",
    )

    setup_gemini.main()

    settings = _read_settings(gemini_dir)
    assert settings["theme"] == "dark"
    assert settings["mcpServers"]["other"] == {"command": "x"}
    assert "trust" not in settings["mcpServers"]["atlassian-mcp"]


def test_does_not_overwrite_unparseable_settings(setup_gemini, tmp_path):
    gemini_dir = tmp_path / ".gemini"
    gemini_dir.mkdir()
    settings_file = gemini_dir / "settings.json"
    original = '// a comment\n{"theme": "dark"}'
    settings_file.write_text(original, encoding="utf-8")

    with pytest.raises(SystemExit, match="Nothing was changed"):
        setup_gemini.main()

    assert settings_file.read_text(encoding="utf-8") == original
    assert not (gemini_dir / "policies").exists()


def test_can_run_repeatedly(setup_gemini, tmp_path):
    setup_gemini.main()
    setup_gemini.main()
    assert "atlassian-mcp" in _read_settings(tmp_path / ".gemini")["mcpServers"]
