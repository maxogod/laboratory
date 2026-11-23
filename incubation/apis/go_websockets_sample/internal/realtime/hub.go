// Package realtime implements the /channels/{channelId}/ws endpoint: a
// per-channel broadcast hub sitting on top of one websocket connection per
// connected chatter.
package realtime

import (
	"context"
	"sync"
)

// Hub is the shared server-side registry of subscribed clients: it fans
// out a message to every client on a channel, and enforces two capacity
// limits — MaxConnections service-wide, MaxConnectionsPerChannel on a
// single channel. Both live here rather than split across Handler/Hub so
// they're checked and updated atomically under one lock.
//
// subscribe/unsubscribe/broadcast share that lock, which also guarantees a
// client is never removed (and its send channel closed) while a broadcast
// to it is still in flight — see client.go.
type Hub struct {
	mu       sync.RWMutex
	channels map[int64]map[*Client]struct{}

	maxConnections           int
	maxConnectionsPerChannel int
	totalConnections         int
	shuttingDown             bool

	wg sync.WaitGroup
}

func NewHub(maxConnections, maxConnectionsPerChannel int) *Hub {
	return &Hub{
		channels:                 make(map[int64]map[*Client]struct{}),
		maxConnections:           maxConnections,
		maxConnectionsPerChannel: maxConnectionsPerChannel,
	}
}

func (h *Hub) hasCapacity(channelID int64) bool {
	h.mu.RLock()
	defer h.mu.RUnlock()

	return h.canAcceptLocked(channelID)
}

func (h *Hub) canAcceptLocked(channelID int64) bool {
	if h.shuttingDown {
		return false
	}
	if h.maxConnections > 0 && h.totalConnections >= h.maxConnections {
		return false
	}
	if h.maxConnectionsPerChannel > 0 && len(h.channels[channelID]) >= h.maxConnectionsPerChannel {
		return false
	}

	return true
}

// subscribe is the authoritative admission check: hasCapacity is only an
// optimistic pre-upgrade hint, this is what actually reserves the slot.
// On success it accounts for the two goroutines (read/write pump) the
// caller is about to start, so Shutdown can wait for them.
func (h *Hub) subscribe(channelID int64, c *Client) bool {
	h.mu.Lock()
	defer h.mu.Unlock()

	if !h.canAcceptLocked(channelID) {
		return false
	}

	if h.channels[channelID] == nil {
		h.channels[channelID] = make(map[*Client]struct{})
	}
	h.channels[channelID][c] = struct{}{}
	h.totalConnections++
	h.wg.Add(2)

	return true
}

func (h *Hub) unsubscribe(channelID int64, c *Client) {
	h.mu.Lock()
	defer h.mu.Unlock()

	if _, ok := h.channels[channelID][c]; !ok {
		return
	}

	delete(h.channels[channelID], c)
	h.totalConnections--
	if len(h.channels[channelID]) == 0 {
		delete(h.channels, channelID)
	}
}

// pumpDone is called once by each of a client's two pumps as they exit.
func (h *Hub) pumpDone() {
	h.wg.Done()
}

// abortSubscription undoes a successful subscribe when the caller decides
// not to start the client's pumps after all (e.g. history replay failed),
// balancing the wg.Add(2) subscribe made on its behalf.
func (h *Hub) abortSubscription(channelID int64, c *Client) {
	h.unsubscribe(channelID, c)
	h.pumpDone()
	h.pumpDone()
}

// broadcast pushes payload to every client subscribed to channelID,
// including whichever client's own send triggered it: clients render
// whatever the server echoes back rather than optimistically rendering
// their own send.
func (h *Hub) broadcast(channelID int64, payload []byte) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	for c := range h.channels[channelID] {
		c.enqueue(payload)
	}
}

// Shutdown asks every connected client to close and blocks until they've
// all finished (both pumps exited) or ctx is done, whichever comes first —
// bounding how long a slow/stuck client can hold up process shutdown. It
// also stops admitting new connections, so this is safe to call exactly
// once. Reports whether every connection drained before ctx expired.
func (h *Hub) Shutdown(ctx context.Context) bool {
	h.mu.Lock()
	h.shuttingDown = true
	clients := make([]*Client, 0, h.totalConnections)
	for _, cs := range h.channels {
		for c := range cs {
			clients = append(clients, c)
		}
	}
	h.mu.Unlock()

	for _, c := range clients {
		c.close()
	}

	drained := make(chan struct{})
	go func() {
		h.wg.Wait()
		close(drained)
	}()

	select {
	case <-drained:
		return true
	case <-ctx.Done():
		return false
	}
}
