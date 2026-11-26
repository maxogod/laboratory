import importlib.util
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Automatically mock environment variables for offline test suite."""
    monkeypatch.setenv("JIRA_BASE_URL", "https://test.atlassian.net")
    monkeypatch.setenv("ATLASSIAN_EMAIL", "test@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "fake_token_123")
    monkeypatch.setenv("BITBUCKET_WORKSPACE", "test-workspace")
    monkeypatch.setenv("BITBUCKET_TOKEN", "fake_app_password")


@pytest.fixture
def load_script(tmp_path, monkeypatch):
    """Load a setup script with its home directory redirected to tmp_path."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    def load(name: str):
        spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / f"{name}.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return load
