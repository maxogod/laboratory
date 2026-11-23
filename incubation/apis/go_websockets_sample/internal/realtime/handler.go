package realtime

import (
	"context"
	"errors"
	"net/http"
	"strconv"
	"time"

	"go_websockets/internal/channels"
	"go_websockets/internal/httpresponse"
	"go_websockets/internal/utils"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
	"go.uber.org/zap"
)

// ChannelService is the subset of channel/message business logic the
// websocket handler depends on. Declared here, on the consumer side,
// rather than next to its implementation in the channels package.
type ChannelService interface {
	GetChannel(ctx context.Context, channelID int64) (*channels.Channel, error)
	ListChannelMessages(ctx context.Context, channelID int64) ([]*channels.Message, error)
	SendMessage(ctx context.Context, channelID, authorID int64, content string) (*channels.Message, error)
	EditMessage(ctx context.Context, channelID, messageID, authorID int64, content string) (*channels.Message, error)
}

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin:     func(r *http.Request) bool { return true },
}

type Handler struct {
	service ChannelService
	hub     *Hub
}

func NewHandler(service ChannelService, hub *Hub) *Handler {
	return &Handler{service: service, hub: hub}
}

// HandleConnection godoc
// @Summary		Open a channel's websocket
// @Description	Upgrades to a websocket connection scoped to channelId. On connect the channel's message history is replayed, then every Message created or edited in the channel is broadcast as it happens. Clients send SendOrEditMessageEvent frames to create or edit messages.
// @Tags			channels
// @Param			channelId	path	int	true	"Channel ID"
// @Success		101	"Switching Protocols"
// @Failure		404	{object}	httpresponse.ErrorResponse	"channel not found"
// @Failure		503	{object}	httpresponse.ErrorResponse	"too many active connections"
// @Router			/channels/{channelId}/ws [get]
//
// Everything before a successful upgrade is a normal gin/HTTP response;
// everything after belongs to the websocket protocol and is handled by the
// Client's pumps instead.
func (h *Handler) HandleConnection(ctx *gin.Context) {
	logger := utils.LoggerFromContext(ctx.Request.Context())

	channelID, err := strconv.ParseInt(ctx.Param("channelId"), 10, 64)
	if err != nil {
		httpresponse.NotFound(ctx, "channel not found")
		return
	}

	if _, err := h.service.GetChannel(ctx.Request.Context(), channelID); err != nil {
		if errors.Is(err, channels.ErrChannelNotFound) {
			httpresponse.NotFound(ctx, err.Error())
			return
		}

		logger.Error("failed to verify channel before websocket upgrade", zap.Error(err))
		httpresponse.InternalServerError(ctx, "failed to open connection")
		return
	}

	if !h.hub.hasCapacity(channelID) {
		httpresponse.ServiceUnavailable(ctx, "too many active connections, try again later")
		return
	}

	conn, err := upgrader.Upgrade(ctx.Writer, ctx.Request, nil)
	if err != nil {
		logger.Warn("websocket upgrade failed", zap.Error(err))
		return
	}

	client := newClient(conn, channelID, logger, h.service, h.hub)

	if !h.hub.subscribe(channelID, client) {
		conn.WriteControl(websocket.CloseMessage,
			websocket.FormatCloseMessage(websocket.CloseTryAgainLater, "too many active connections"),
			time.Now().Add(writeWait))
		conn.Close()
		return
	}

	if err := client.replayHistory(ctx.Request.Context()); err != nil {
		logger.Error("failed to replay message history", zap.Error(err))
		h.hub.abortSubscription(channelID, client)
		conn.Close()
		return
	}

	go client.writePump()
	go client.readPump()
}
