#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

cleanup() {
	docker compose -f docker-compose.test.yml down -v
}
trap cleanup EXIT

docker compose -f docker-compose.test.yml up -d --build

RUN_E2E=1 go test ./test/e2e/... -v
