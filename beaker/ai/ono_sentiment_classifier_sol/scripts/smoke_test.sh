#!/usr/bin/env bash
# End-to-end smoke test on a small subset.
set -euo pipefail
cd "$(dirname "$0")/.."

export MAX_ROWS="${MAX_ROWS:-10000}"
export N_FEATURES="${N_FEATURES:-500}"
export MAX_EPOCHS="${MAX_EPOCHS:-2}"

cleanup() { docker compose down --remove-orphans >/dev/null 2>&1 || true; }
trap cleanup EXIT

rm -f models/sentiment.safetensors models/loss_history.json

echo "==> build"
docker compose build

echo "==> preprocess (MAX_ROWS=$MAX_ROWS N_FEATURES=$N_FEATURES)"
docker compose run --rm --no-deps orchestrator preprocess

echo "==> train (MAX_EPOCHS=$MAX_EPOCHS, 3 workers)"
docker compose up --abort-on-container-exit --exit-code-from orchestrator orchestrator

echo "==> checks"
test -s models/sentiment.safetensors || { echo "FAIL: no safetensors"; exit 1; }
test -s models/loss_history.json     || { echo "FAIL: no loss history"; exit 1; }

echo "==> evaluate"
OUT="$(docker compose run --rm --no-deps orchestrator evaluate)"
echo "$OUT"

python3 - "$OUT" <<'PY'
import json, re, sys
loss = json.load(open("models/loss_history.json"))
assert loss, "FAIL: empty loss history"
print(f"loss: first={loss[0]:.4f} last={loss[-1]:.4f} epochs={len(loss)}")
assert loss[-1] < loss[0], "FAIL: loss did not decrease"
acc = float(re.search(r"accuracy: ([0-9.]+)", sys.argv[1]).group(1))
assert acc > 1 / 3, f"FAIL: accuracy {acc} not above chance - suspect model.py layout/activations"
print(f"accuracy {acc:.4f} > chance: OK")
PY
echo "SMOKE TEST PASSED"
