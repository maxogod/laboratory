package e2e

import (
	"encoding/json"
	"fmt"
	"net/http"
	"testing"
	"time"

	"github.com/gorilla/websocket"
)

func dialChannelWS(t *testing.T, channelID int64) *websocket.Conn {
	t.Helper()

	conn, _, err := websocket.DefaultDialer.Dial(fmt.Sprintf("%s/channels/%d/ws", wsURL, channelID), nil)
	if err != nil {
		t.Fatalf("dial ws: %v", err)
	}

	return conn
}

func send(t *testing.T, conn *websocket.Conn, payload map[string]any) {
	t.Helper()

	b, err := json.Marshal(payload)
	if err != nil {
		t.Fatalf("marshal payload: %v", err)
	}
	if err := conn.WriteMessage(websocket.TextMessage, b); err != nil {
		t.Fatalf("write message: %v", err)
	}
}

func readFrame[T any](t *testing.T, conn *websocket.Conn) T {
	t.Helper()

	conn.SetReadDeadline(time.Now().Add(3 * time.Second))
	_, raw, err := conn.ReadMessage()
	if err != nil {
		t.Fatalf("read message: %v", err)
	}

	var v T
	if err := json.Unmarshal(raw, &v); err != nil {
		t.Fatalf("unmarshal %s: %v", raw, err)
	}

	return v
}

func TestWebsocket_UnknownChannel_RejectsUpgradeWith404(t *testing.T) {
	resp, err := http.Get(fmt.Sprintf("%s/channels/%d/ws", baseURL, unlikelyChannelID))
	if err != nil {
		t.Fatalf("get: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusNotFound {
		t.Fatalf("expected 404, got %d", resp.StatusCode)
	}
}

func TestWebsocket_SendBroadcastsToAllSubscribers(t *testing.T) {
	channel := createChannel(t, uniqueName())

	a := dialChannelWS(t, channel.ID)
	defer a.Close()
	b := dialChannelWS(t, channel.ID)
	defer b.Close()

	send(t, a, map[string]any{"authorId": 1, "content": "hello from A"})

	toA := readFrame[messageResponse](t, a)
	if toA.Content != "hello from A" {
		t.Fatalf("sender: expected 'hello from A', got %q", toA.Content)
	}

	toB := readFrame[messageResponse](t, b)
	if toB.ID != toA.ID {
		t.Fatalf("subscriber did not receive the same message broadcast")
	}
}

func TestWebsocket_EditByOriginalAuthor_Broadcasts(t *testing.T) {
	channel := createChannel(t, uniqueName())
	conn := dialChannelWS(t, channel.ID)
	defer conn.Close()

	send(t, conn, map[string]any{"authorId": 7, "content": "v1"})
	created := readFrame[messageResponse](t, conn)

	send(t, conn, map[string]any{"id": created.ID, "authorId": 7, "content": "v2"})
	edited := readFrame[messageResponse](t, conn)

	if edited.Content != "v2" {
		t.Fatalf("expected content 'v2', got %q", edited.Content)
	}
	if edited.EditedAt == nil {
		t.Fatalf("expected editedAt to be set after an edit")
	}
	if !edited.CreatedAt.Equal(created.CreatedAt) {
		t.Fatalf("expected createdAt to be unchanged by an edit: before %v, after %v", created.CreatedAt, edited.CreatedAt)
	}
}

func TestWebsocket_SendPersistsTheExactBroadcastTimestamp(t *testing.T) {
	channel := createChannel(t, uniqueName())
	conn := dialChannelWS(t, channel.ID)
	defer conn.Close()

	send(t, conn, map[string]any{"authorId": 1, "content": "checked against storage"})
	broadcast := readFrame[messageResponse](t, conn)

	resp, err := http.Get(fmt.Sprintf("%s/channels/%d/messages", baseURL, channel.ID))
	if err != nil {
		t.Fatalf("get: %v", err)
	}
	defer resp.Body.Close()

	var env envelope[[]messageResponse]
	if err := json.NewDecoder(resp.Body).Decode(&env); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if len(env.Data) != 1 {
		t.Fatalf("expected 1 persisted message, got %d", len(env.Data))
	}

	persisted := env.Data[0]
	if persisted.ID != broadcast.ID || !persisted.CreatedAt.Equal(broadcast.CreatedAt) {
		t.Fatalf("persisted message %+v does not match broadcast %+v", persisted, broadcast)
	}
}

func TestWebsocket_RejectsAuthorIDLargerThanInt32(t *testing.T) {
	channel := createChannel(t, uniqueName())
	conn := dialChannelWS(t, channel.ID)
	defer conn.Close()

	send(t, conn, map[string]any{"authorId": 2147483648, "content": "overflow"})
	errResp := readFrame[errorFrame](t, conn)

	if errResp.Error == "" {
		t.Fatalf("expected a non-empty error message")
	}
}

func TestWebsocket_EditByWrongAuthor_RejectsButKeepsConnectionOpen(t *testing.T) {
	channel := createChannel(t, uniqueName())
	conn := dialChannelWS(t, channel.ID)
	defer conn.Close()

	send(t, conn, map[string]any{"authorId": 1, "content": "mine"})
	created := readFrame[messageResponse](t, conn)

	send(t, conn, map[string]any{"id": created.ID, "authorId": 999, "content": "hijack"})
	errResp := readFrame[errorFrame](t, conn)
	if errResp.Error == "" {
		t.Fatalf("expected a non-empty error message")
	}

	send(t, conn, map[string]any{"authorId": 1, "content": "still here"})
	still := readFrame[messageResponse](t, conn)
	if still.Content != "still here" {
		t.Fatalf("connection did not survive the rejected edit")
	}
}

func TestWebsocket_BlankContent_ReturnsValidationErrorFrame(t *testing.T) {
	channel := createChannel(t, uniqueName())
	conn := dialChannelWS(t, channel.ID)
	defer conn.Close()

	send(t, conn, map[string]any{"authorId": 1, "content": "   "})
	errResp := readFrame[errorFrame](t, conn)

	if errResp.Error == "" {
		t.Fatalf("expected a non-empty error message")
	}
}

func TestWebsocket_ContentLengthIsCountedInCharactersNotBytes(t *testing.T) {
	channel := createChannel(t, uniqueName())
	conn := dialChannelWS(t, channel.ID)
	defer conn.Close()

	// 2000 multi-byte characters: well over 2000 bytes, exactly 2000 runes.
	content := ""
	for i := 0; i < 2000; i++ {
		content += "é"
	}

	send(t, conn, map[string]any{"authorId": 1, "content": content})
	got := readFrame[messageResponse](t, conn)

	if got.Content != content {
		t.Fatalf("expected a 2000-character message to be accepted")
	}
}

func TestWebsocket_HistoryReplayOnConnect(t *testing.T) {
	channel := createChannel(t, uniqueName())

	writer := dialChannelWS(t, channel.ID)
	send(t, writer, map[string]any{"authorId": 1, "content": "old message 1"})
	readFrame[messageResponse](t, writer)
	send(t, writer, map[string]any{"authorId": 1, "content": "old message 2"})
	readFrame[messageResponse](t, writer)
	writer.Close()

	reader := dialChannelWS(t, channel.ID)
	defer reader.Close()

	first := readFrame[messageResponse](t, reader)
	second := readFrame[messageResponse](t, reader)

	if first.Content != "old message 1" || second.Content != "old message 2" {
		t.Fatalf("expected history replay in order, got %q then %q", first.Content, second.Content)
	}
}

// TestWebsocket_MaxConnectionsPerChannel_RejectsOverflow relies on
// WS_MAX_CONNECTIONS_PER_CHANNEL=3, set in docker-compose.test.yml.
func TestWebsocket_MaxConnectionsPerChannel_RejectsOverflow(t *testing.T) {
	channel := createChannel(t, uniqueName())

	conns := make([]*websocket.Conn, 3)
	for i := range conns {
		conns[i] = dialChannelWS(t, channel.ID)
	}
	defer func() {
		for _, c := range conns {
			c.Close()
		}
	}()

	_, resp, err := websocket.DefaultDialer.Dial(fmt.Sprintf("%s/channels/%d/ws", wsURL, channel.ID), nil)
	if err == nil {
		t.Fatalf("expected the connection past the per-channel cap to be rejected")
	}
	if resp == nil || resp.StatusCode != http.StatusServiceUnavailable {
		t.Fatalf("expected 503, got response %v (err: %v)", resp, err)
	}
}
