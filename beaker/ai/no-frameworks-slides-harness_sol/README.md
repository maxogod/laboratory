# Slides agent

A presentation html slides agent built from scratch with only the Python standard library (no SDKs, no frameworks).
It calls an LLM through OpenRouter, runs the structured tool calls the model returns, and loops until
the model replies without any tool calls or hits limit.

## Setup

Requires Python and [uv](https://docs.astral.sh/uv/).

```
cp .env.example .env     # then set MODEL_PROVIDER and MODEL_PROVIDER_API_KEY
```

| Variable               | Default                       | Meaning                                |
| ---------------------- | ----------------------------- | -------------------------------------- |
| `MODEL_PROVIDER`       | (required)                    | `open-router` or `local-ollama`        |
| `MODEL_PROVIDER_API_KEY` | (required for open-router)  | Provider API key                       |
| `AGENT_MODEL`          | `openrouter/free` (open-router); required for local-ollama | Any model that supports tools |
| `AGENT_WORKSPACE`      | `./workspace`                 | Directory the file tools may touch     |
| `AGENT_MAX_ITERATIONS` | `25`                          | Model calls allowed per user message   |
| `MODEL_PROVIDER_BASE_URL` | `https://openrouter.ai/api/v1` / `http://localhost:11434` | API base URL (per provider) |

## Run

```bash
uv run agent [-v]                               # new session
uv run agent --resume sessions/<id>.json   # continue a saved session
```

## Layout

```bash
src/agent/
  main.py                        # CLI and stdin prompt loop
  config.py                      # .env loading and settings
  logging.py                     # stderr logging
  model/base.py                  # ModelClient interface, ToolCall, ModelResponse
  model/openrouter.py            # urllib client for OpenRouter
  harness/loop.py                # the agent loop
  harness/context.py             # message list + session persistence
  harness/prompts.py             # system prompt
  tools/registry.py              # @registry.tool decorator, schema export, execution
  tools/web.py                   # fetch_url
  tools/html_file_operations.py  # list/read/write HTML files in the workspace
```

