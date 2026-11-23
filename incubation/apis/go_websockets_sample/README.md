# Go websockets

## End-to-end tests

`test/e2e` drives the real REST and WebSocket endpoints over the network — no mocks, real Postgres. It expects a running server (`docker-compose.test.yml` spins up an isolated `api` + `db` and never touches the dev database):

```sh
./scripts/e2e-test.sh
```

That builds the image, starts the stack, runs the suite, and tears the stack down afterwards regardless of pass/fail. The tests only run when `RUN_E2E=1` is set — a plain `go test ./...` skips this package instantly instead of hanging trying to reach a server that isn't there. To run against a server you're already running elsewhere: `RUN_E2E=1 E2E_BASE_URL=http://localhost:PORT go test ./test/e2e/...`.
