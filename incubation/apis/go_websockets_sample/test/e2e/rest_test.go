package e2e

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"testing"
)

func TestCreateChannel_Success(t *testing.T) {
	channel := createChannel(t, uniqueName())

	if channel.ID == 0 {
		t.Fatalf("expected non-zero id")
	}
	if channel.CreatedAt.IsZero() {
		t.Fatalf("expected createdAt to be set")
	}
}

func TestCreateChannel_DuplicateName(t *testing.T) {
	name := uniqueName()
	createChannel(t, name)

	body, _ := json.Marshal(map[string]string{"name": name})
	resp, err := http.Post(baseURL+"/channels", "application/json", bytes.NewReader(body))
	if err != nil {
		t.Fatalf("post: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", resp.StatusCode)
	}
	if ct := resp.Header.Get("Content-Type"); ct != "application/problem+json" {
		t.Fatalf("expected application/problem+json, got %q", ct)
	}

	var p problem
	if err := json.NewDecoder(resp.Body).Decode(&p); err != nil {
		t.Fatalf("decode problem: %v", err)
	}
	if p.Status != http.StatusBadRequest {
		t.Fatalf("expected problem.status 400, got %d", p.Status)
	}
}

func TestCreateChannel_DuplicateNameIgnoringCase(t *testing.T) {
	name := uniqueName()
	createChannel(t, name)

	body, _ := json.Marshal(map[string]string{"name": strings.ToUpper(name)})
	resp, err := http.Post(baseURL+"/channels", "application/json", bytes.NewReader(body))
	if err != nil {
		t.Fatalf("post: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusBadRequest {
		t.Fatalf("expected 400 for a case-insensitive duplicate, got %d", resp.StatusCode)
	}
}

func TestCreateChannel_RejectsUnrepresentableCharacters(t *testing.T) {
	body, _ := json.Marshal(map[string]string{"name": uniqueName() + "\x00"})
	resp, err := http.Post(baseURL+"/channels", "application/json", bytes.NewReader(body))
	if err != nil {
		t.Fatalf("post: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 400 || resp.StatusCode >= 500 {
		t.Fatalf("expected a 4xx client error, got %d", resp.StatusCode)
	}
}

func TestCreateChannel_BlankName(t *testing.T) {
	body, _ := json.Marshal(map[string]string{"name": "   "})
	resp, err := http.Post(baseURL+"/channels", "application/json", bytes.NewReader(body))
	if err != nil {
		t.Fatalf("post: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", resp.StatusCode)
	}
}

func TestListChannels_IncludesCreated(t *testing.T) {
	channel := createChannel(t, uniqueName())

	resp, err := http.Get(baseURL + "/channels")
	if err != nil {
		t.Fatalf("get: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Fatalf("expected 200, got %d", resp.StatusCode)
	}

	var env envelope[[]channelResponse]
	if err := json.NewDecoder(resp.Body).Decode(&env); err != nil {
		t.Fatalf("decode: %v", err)
	}

	for _, c := range env.Data {
		if c.ID == channel.ID {
			return
		}
	}
	t.Fatalf("expected channel %d in list of %d channels", channel.ID, len(env.Data))
}

func TestGetChannelMessages_EmptyForNewChannel(t *testing.T) {
	channel := createChannel(t, uniqueName())

	resp, err := http.Get(fmt.Sprintf("%s/channels/%d/messages", baseURL, channel.ID))
	if err != nil {
		t.Fatalf("get: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Fatalf("expected 200, got %d", resp.StatusCode)
	}

	var env envelope[[]messageResponse]
	if err := json.NewDecoder(resp.Body).Decode(&env); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if len(env.Data) != 0 {
		t.Fatalf("expected no messages, got %d", len(env.Data))
	}
}

func TestGetChannelMessages_ChannelNotFound(t *testing.T) {
	resp, err := http.Get(fmt.Sprintf("%s/channels/%d/messages", baseURL, unlikelyChannelID))
	if err != nil {
		t.Fatalf("get: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusNotFound {
		t.Fatalf("expected 404, got %d", resp.StatusCode)
	}
}

const unlikelyChannelID = 999_999_999
