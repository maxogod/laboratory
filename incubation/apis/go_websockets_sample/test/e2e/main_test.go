// Package e2e exercises the running service over real HTTP/WebSocket
// connections. It expects the stack from docker-compose.test.yml (or an
// equivalent server) to already be up — see scripts/e2e-test.sh.
//
// These tests only run when RUN_E2E is set, so a plain `go test ./...`
// doesn't hang or fail trying to reach a server that isn't there.
package e2e

import (
	"fmt"
	"net/http"
	"os"
	"strings"
	"testing"
	"time"
)

var (
	baseURL string
	wsURL   string
)

func TestMain(m *testing.M) {
	if os.Getenv("RUN_E2E") == "" {
		fmt.Println("e2e: skipping, RUN_E2E is not set (see scripts/e2e-test.sh)")
		os.Exit(0)
	}

	baseURL = strings.TrimRight(envOrDefault("E2E_BASE_URL", "http://localhost:18080"), "/")
	wsURL = "ws" + strings.TrimPrefix(baseURL, "http")

	if err := waitForReady(30 * time.Second); err != nil {
		fmt.Fprintln(os.Stderr, "e2e: server never became ready:", err)
		os.Exit(1)
	}

	os.Exit(m.Run())
}

func envOrDefault(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

func waitForReady(timeout time.Duration) error {
	deadline := time.Now().Add(timeout)

	var lastErr error
	for time.Now().Before(deadline) {
		resp, err := http.Get(baseURL + "/channels")
		if err != nil {
			lastErr = err
		} else {
			resp.Body.Close()
			if resp.StatusCode == http.StatusOK {
				return nil
			}
			lastErr = fmt.Errorf("unexpected status %d", resp.StatusCode)
		}

		time.Sleep(500 * time.Millisecond)
	}

	return lastErr
}
