import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


PROVIDERS = {
    "open-router": ("https://openrouter.ai/api/v1", "openrouter/free", True),
    "local-ollama": ("http://localhost:11434", None, False),
}


@dataclass(frozen=True)
class Config:
    provider: str
    api_key: str
    model: str
    base_url: str
    workspace: Path
    max_iterations: int

    @classmethod
    def from_env(cls) -> Config:
        load_dotenv()
        provider = os.environ.get("MODEL_PROVIDER", "")
        if provider not in PROVIDERS:
            raise SystemExit(
                f"MODEL_PROVIDER must be one of {', '.join(PROVIDERS)} "
                "(see .env.example)"
            )
        provider_url, default_model, key_required = PROVIDERS[provider]
        api_key = os.environ.get("MODEL_PROVIDER_API_KEY", "")
        if key_required and not api_key:
            raise SystemExit("MODEL_PROVIDER_API_KEY is not set (see .env.example)")
        model = os.environ.get("AGENT_MODEL", default_model)
        if not model:
            raise SystemExit(f"AGENT_MODEL is required for {provider}")
        workspace = Path(os.environ.get("AGENT_WORKSPACE", "./workspace")).resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        return cls(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=provider_url,
            workspace=workspace,
            max_iterations=int(os.environ.get("AGENT_MAX_ITERATIONS", "25")),
        )
