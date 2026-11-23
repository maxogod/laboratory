import argparse
import sys
from datetime import datetime
from pathlib import Path

from agent.config import Config
from agent.harness.context import Context
from agent.harness.loop import run
from agent.harness.prompts import SYSTEM_PROMPT
from agent.logging import setup_logging
from agent.model.local_ollama import LocalOllamaClient
from agent.model.openrouter import OpenRouterClient
from agent.tools import build_registry


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agent", description="HTML slide-making agent"
    )
    parser.add_argument(
        "--resume", type=Path, metavar="SAVE_FILE.json", help="continue a saved session"
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    log = setup_logging(args.verbose)
    config = Config.from_env()
    client_cls = (
        OpenRouterClient if config.provider == "open-router" else LocalOllamaClient
    )
    model = client_cls(config.api_key, config.model, config.base_url)
    registry = build_registry(config.workspace)

    if args.resume:
        ctx = Context.load(args.resume)
        log.info("resumed %s (%d messages)", args.resume, len(ctx.messages))
    else:
        save_path = Path("sessions") / f"{datetime.now():%Y%m%d-%H%M%S}.json"
        ctx = Context.new(SYSTEM_PROMPT, save_path)
        log.info("saving session to %s", save_path)

    while True:
        try:
            task = input("> ").strip()
        except EOFError:
            break
        if task in ("", "exit", "quit"):
            break
        ctx.add_user(task)
        try:
            print(run(ctx, model, registry, config.max_iterations))
        except RuntimeError as e:
            print(f"error: {e}", file=sys.stderr)
