# atlassian-mcp

[![Python Version](https://img.shields.io/badge/python-3.14%2B-blue)](https://www.python.org/)
[![Tooling](https://img.shields.io/badge/managed%20by-uv-de5b43)](https://github.com/astral-sh/uv)

MCP server that lets Agents read and write Jira tickets and Bitbucket pull requests.

## 🏗️ Architecture & Extensibility

Uses a **Modular Provider Pattern**:
* **`core/`**: Centralizes HTTP client management, auth handling, error boundaries, and shared MCP context.
* **`integrations/`**: Houses self-contained integration modules ([`jira`](docs/jira-tools.md), [`bitbucket`](docs/bitbucket-tools.md), [`storybook`](docs/storybook-tools.md)). Each module contains its own API client, data models, and tool definitions.
* **Feature Flags**: Integrations initialize gracefully based on available environment variables. Missing credentials for unused integrations won't crash the server.

---

## 🚀 Quickstart with `uv`

### Prerequisites

Install [uv](https://github.com/astral-sh/uv) if you haven't already:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Configuration & Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and configure your credentials. The tokens need write access to create and edit content:
   * **`BITBUCKET_TOKEN`**: `read:pullrequest:bitbucket`, `write:pullrequest:bitbucket` and `read:repository:bitbucket`.
   * **`JIRA_API_TOKEN`**: uses your Jira account's permissions. A scoped token needs `read:jira-work` and `write:jira-work`.

3. Sync project dependencies and create the virtual environment:
   ```bash
   uv sync
   ```

---

## 💻 Development & Testing

All essential developement commands:

**Run local development server:**
```bash
uv run atlassian-mcp
```

**Run unit tests:**
```bash
uv run pytest
```

**Linter utils**
```bash
uv run ruff check --fix
uv run ruff format --check
uv run ruff format

uv run mypy src tests
```
