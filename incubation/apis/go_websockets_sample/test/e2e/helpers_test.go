package e2e

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"sync/atomic"
	"testing"
	"time"
)

type envelope[T any] struct {
	Data T `json:"data"`
}

type problem struct {
	Type     string `json:"type"`
	Title    string `json:"title"`
	Status   int    `json:"status"`
	Detail   string `json:"detail"`
	Instance string `json:"instance"`
}

// errorFrame is the websocket error frame shape: {"error": "<message>"},
// distinct from the REST problem+json body above.
type errorFrame struct {
	Error string `json:"error"`
}

type channelResponse struct {
	ID        int64     `json:"id"`
	Name      string    `json:"name"`
	CreatedAt time.Time `json:"createdAt"`
}

type messageResponse struct {
	ID        int64      `json:"id"`
	ChannelID int64      `json:"channelId"`
	AuthorID  int64      `json:"authorId"`
	Content   string     `json:"content"`
	CreatedAt time.Time  `json:"createdAt"`
	EditedAt  *time.Time `json:"editedAt"`
}

var nameCounter atomic.Int64

// uniqueName stays well under the API's 50-char channel name limit.
func uniqueName() string {
	return fmt.Sprintf("e2e-%d-%d", time.Now().UnixNano(), nameCounter.Add(1))
}

func createChannel(t *testing.T, name string) channelResponse {
	t.Helper()

	body, _ := json.Marshal(map[string]string{"name": name})
	resp, err := http.Post(baseURL+"/channels", "application/json", bytes.NewReader(body))
	if err != nil {
		t.Fatalf("create channel: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		t.Fatalf("create channel: expected 201, got %d", resp.StatusCode)
	}

	var env envelope[channelResponse]
	if err := json.NewDecoder(resp.Body).Decode(&env); err != nil {
		t.Fatalf("decode channel: %v", err)
	}

	return env.Data
}
