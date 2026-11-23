#!/usr/bin/env bash
# Short learning-rate trial on a subset, isolated from the full data/model
# (writes to data/trial and models/trial). Usage: scripts/lr_trial.sh [lr ...]
set -euo pipefail
cd "$(dirname "$0")/.."

LRS=("$@"); [ ${#LRS[@]} -gt 0 ] || LRS=(0.5 1.0 2.0)
export MAX_ROWS="${MAX_ROWS:-60000}" MAX_EPOCHS="${MAX_EPOCHS:-10}"
export PROCESSED_DIR=data/trial MODELS_DIR=models/trial OPTIMIZER="${OPTIMIZER:-gd}"
trap 'docker compose down --remove-orphans >/dev/null 2>&1 || true' EXIT

docker compose run --rm --no-deps orchestrator preprocess
for lr in "${LRS[@]}"; do
  echo "=== OPTIMIZER=$OPTIMIZER LR=$lr MAX_ROWS=$MAX_ROWS MAX_EPOCHS=$MAX_EPOCHS ==="
  LR="$lr" docker compose up --abort-on-container-exit --exit-code-from orchestrator orchestrator 2>&1 | grep -E "avg_loss|optimizer=" | tail -3
  docker compose run --rm --no-deps orchestrator evaluate 2>/dev/null | grep -E "^accuracy|negative|neutral|positive"
done
