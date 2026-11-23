package realtime

import (
	"context"
	"encoding/json"
	"errors"
	"math"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"go_websockets/internal/channels"
	"go_websockets/internal/utils"

	"github.com/gorilla/websocket"
	"go.uber.org/zap"
)

const (
	// maxMessageBytes caps a single incoming frame; gorilla enforces this
	// itself and sends a close frame to the peer when it's exceeded. Sized
	// for the worst case: 2000 characters at 4 bytes each (astral-plane
	// UTF-8) plus JSON escaping and field overhead.
	maxMessageBytes = 32 * 1024

	// pingPeriod must be shorter than pongWait so a ping always has time
	// to round-trip before the peer is considered dead.
	pongWait   = 60 * time.Second
	pingPeriod = pongWait * 9 / 10

	writeWait      = 10 * time.Second
	sendBufferSize = 16
	eventTimeout   = 5 * time.Second
)

var nextConnID atomic.Int64

// SendOrEditMessageEvent is the payload a client sends over the websocket
// to create (ID omitted) or edit (ID set) a message.
type SendOrEditMessageEvent struct {
	ID       *int64 `json:"id,omitempty"`
	AuthorID int64  `json:"authorId"`
	Content  string `json:"content"`
}

// errorFrame is the shape of a server->client error message.
type errorFrame struct {
	Error string `json:"error"`
}

// Client is one websocket connection scoped to a single channel. Many
// Clients subscribe to the same channel at once, one per connected
// chatter, via the Hub.
type Client struct {
	conn      *websocket.Conn
	channelID int64
	logger    *zap.Logger
	service   ChannelService
	hub       *Hub

	send      chan []byte
	done      chan struct{}
	closeOnce sync.Once
}

func newClient(conn *websocket.Conn, channelID int64, logger *zap.Logger, service ChannelService, hub *Hub) *Client {
	return &Client{
		conn:      conn,
		channelID: channelID,
		logger: logger.With(
			zap.Int64("channel_id", channelID),
			zap.Int64("ws_conn_id", nextConnID.Add(1)),
		),
		service: service,
		hub:     hub,
		send:    make(chan []byte, sendBufferSize),
		done:    make(chan struct{}),
	}
}

// readPump is the only goroutine that calls conn.ReadMessage. It runs
// until the connection errors, including a pong deadline timeout.
func (c *Client) readPump() {
	defer func() {
		c.hub.unsubscribe(c.channelID, c)
		close(c.send)
		c.conn.Close()
		c.hub.pumpDone()
	}()

	c.conn.SetReadLimit(maxMessageBytes)
	c.conn.SetReadDeadline(time.Now().Add(pongWait))
	c.conn.SetPongHandler(func(string) error {
		c.conn.SetReadDeadline(time.Now().Add(pongWait))
		return nil
	})

	for {
		_, raw, err := c.conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err,
				websocket.CloseGoingAway, websocket.CloseNormalClosure, websocket.CloseNoStatusReceived) {
				c.logger.Warn("websocket connection closed unexpectedly", zap.Error(err))
			}
			return
		}

		c.handleEvent(raw)
	}
}

// replayHistory sends the channel's existing messages directly over the
// connection, then drains anything the Hub already queued in c.send during
// that fetch — deduping by id — so a message that arrives mid-replay is
// delivered exactly once instead of missed or duplicated. Must run after
// the caller has subscribed to the Hub and before the pumps start, since
// nothing else is writing to the connection yet.
func (c *Client) replayHistory(ctx context.Context) error {
	messages, err := c.service.ListChannelMessages(ctx, c.channelID)
	if err != nil {
		return err
	}

	seen := make(map[int64]struct{}, len(messages))
	for _, m := range messages {
		payload, err := json.Marshal(channels.ToMessageResponse(m))
		if err != nil {
			return err
		}
		if err := c.conn.WriteMessage(websocket.TextMessage, payload); err != nil {
			return err
		}
		seen[m.ID] = struct{}{}
	}

	for {
		select {
		case payload := <-c.send:
			var queued struct {
				ID int64 `json:"id"`
			}
			if err := json.Unmarshal(payload, &queued); err == nil {
				if _, dup := seen[queued.ID]; dup {
					continue
				}
			}
			if err := c.conn.WriteMessage(websocket.TextMessage, payload); err != nil {
				return err
			}
		default:
			return nil
		}
	}
}

func (c *Client) handleEvent(raw []byte) {
	var event SendOrEditMessageEvent
	if err := json.Unmarshal(raw, &event); err != nil {
		c.sendError("invalid message payload: " + err.Error())
		return
	}

	if event.AuthorID < 1 || event.AuthorID > math.MaxInt32 {
		c.sendError("authorId must be a positive 32-bit integer")
		return
	}

	if strings.TrimSpace(event.Content) == "" {
		c.sendError("content is required")
		return
	}

	ctx, cancel := context.WithTimeout(utils.WithLogger(context.Background(), c.logger), eventTimeout)
	defer cancel()

	var (
		message *channels.Message
		err     error
	)

	if event.ID == nil {
		message, err = c.service.SendMessage(ctx, c.channelID, event.AuthorID, event.Content)
	} else {
		message, err = c.service.EditMessage(ctx, c.channelID, *event.ID, event.AuthorID, event.Content)
	}

	if err != nil {
		c.handleServiceError(err)
		return
	}

	payload, err := json.Marshal(channels.ToMessageResponse(message))
	if err != nil {
		c.logger.Error("failed to marshal outgoing message", zap.Error(err))
		return
	}

	c.hub.broadcast(c.channelID, payload)
}

func (c *Client) handleServiceError(err error) {
	switch {
	case errors.Is(err, channels.ErrInvalidMessageContent),
		errors.Is(err, channels.ErrMessageNotFound),
		errors.Is(err, channels.ErrMessageAuthorMismatch),
		errors.Is(err, channels.ErrChannelNotFound):
		c.sendError(err.Error())
	default:
		c.logger.Error("failed to process websocket event", zap.Error(err))
		c.sendError("failed to process message")
	}
}

// sendError queues an error frame to this client only; the connection
// stays open.
func (c *Client) sendError(detail string) {
	payload, err := json.Marshal(errorFrame{Error: detail})
	if err != nil {
		c.logger.Error("failed to marshal error frame", zap.Error(err))
		return
	}

	c.enqueue(payload)
}

// enqueue is non-blocking: a client too slow to drain its buffer gets
// evicted instead of stalling broadcast for everyone else (broadcast
// calls this while holding the Hub's read lock).
func (c *Client) enqueue(payload []byte) {
	select {
	case c.send <- payload:
	default:
		c.logger.Warn("client send buffer full, closing connection")
		c.close()
	}
}

// writePump is the only goroutine that calls conn.WriteMessage — gorilla
// connections don't support concurrent writers, so every outbound frame
// (data, ping, close) is funneled through here.
func (c *Client) writePump() {
	ticker := time.NewTicker(pingPeriod)
	defer func() {
		ticker.Stop()
		c.conn.Close()
		c.hub.pumpDone()
	}()

	for {
		select {
		case payload, ok := <-c.send:
			c.conn.SetWriteDeadline(time.Now().Add(writeWait))
			if !ok {
				c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}
			if err := c.conn.WriteMessage(websocket.TextMessage, payload); err != nil {
				return
			}

		case <-ticker.C:
			c.conn.SetWriteDeadline(time.Now().Add(writeWait))
			if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}

		case <-c.done:
			c.conn.SetWriteDeadline(time.Now().Add(writeWait))
			c.conn.WriteMessage(websocket.CloseMessage,
				websocket.FormatCloseMessage(websocket.CloseGoingAway, "server shutting down"))
			return
		}
	}
}

// close requests a graceful shutdown of this connection; safe to call more
// than once or concurrently.
func (c *Client) close() {
	c.closeOnce.Do(func() {
		close(c.done)
	})
}
