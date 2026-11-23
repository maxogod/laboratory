package channels

import (
	"context"
	"errors"
	"net/http"
	"strconv"

	"go_websockets/internal/httpresponse"
	"go_websockets/internal/utils"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// ChannelsService is the business-logic contract the handler depends on.
// Declared here, on the consumer side, rather than next to its
// implementation in services.go.
type ChannelsService interface {
	CreateChannel(ctx context.Context, name string) (*Channel, error)
	ListChannels(ctx context.Context) ([]*Channel, error)
	ListChannelMessages(ctx context.Context, channelID int64) ([]*Message, error)
}

type ChannelsHandler struct {
	service ChannelsService
}

func NewChannelsHandler(service ChannelsService) *ChannelsHandler {
	return &ChannelsHandler{
		service: service,
	}
}

// CreateChannel godoc
// @Summary		Create a channel
// @Description	Creates a new channel with a unique name.
// @Tags			channels
// @Accept			json
// @Produce		json
// @Param			request	body		CreateChannelRequest	true	"Channel to create"
// @Success		201		{object}	httpresponse.Envelope{data=ChannelResponse}
// @Failure		400		{object}	httpresponse.ErrorResponse	"invalid or duplicate name"
// @Router			/channels [post]
func (h *ChannelsHandler) CreateChannel(ctx *gin.Context) {
	logger := utils.LoggerFromContext(ctx.Request.Context())

	var req CreateChannelRequest
	if err := ctx.ShouldBindJSON(&req); err != nil {
		logger.Warn("invalid create channel request", zap.Error(err))
		httpresponse.BadRequest(ctx, "invalid request body: "+err.Error())
		return
	}

	channel, err := h.service.CreateChannel(ctx.Request.Context(), req.Name)
	if err != nil {
		switch {
		case errors.Is(err, ErrChannelNameExists), errors.Is(err, ErrInvalidChannelName):
			httpresponse.BadRequest(ctx, err.Error())
		default:
			logger.Error("failed to create channel", zap.Error(err))
			httpresponse.InternalServerError(ctx, "failed to create channel")
		}
		return
	}

	httpresponse.JSON(ctx, http.StatusCreated, ToChannelResponse(channel))
}

// GetChannelList godoc
// @Summary		List channels
// @Description	Returns all channels ordered by createdAt ascending.
// @Tags			channels
// @Produce		json
// @Success		200	{object}	httpresponse.Envelope{data=[]ChannelResponse}
// @Router			/channels [get]
func (h *ChannelsHandler) GetChannelList(ctx *gin.Context) {
	logger := utils.LoggerFromContext(ctx.Request.Context())

	channels, err := h.service.ListChannels(ctx.Request.Context())
	if err != nil {
		logger.Error("failed to list channels", zap.Error(err))
		httpresponse.InternalServerError(ctx, "failed to list channels")
		return
	}

	httpresponse.JSON(ctx, http.StatusOK, ToChannelResponses(channels))
}

// GetChannelMessages godoc
// @Summary		List a channel's message history
// @Description	Returns the channel's messages ordered by createdAt then id ascending.
// @Tags			channels
// @Produce		json
// @Param			channelId	path		int	true	"Channel ID"
// @Success		200			{object}	httpresponse.Envelope{data=[]MessageResponse}
// @Failure		404			{object}	httpresponse.ErrorResponse	"channel not found"
// @Router			/channels/{channelId}/messages [get]
func (h *ChannelsHandler) GetChannelMessages(ctx *gin.Context) {
	logger := utils.LoggerFromContext(ctx.Request.Context())

	channelID, err := strconv.ParseInt(ctx.Param("channelId"), 10, 64)
	if err != nil {
		httpresponse.NotFound(ctx, "channel not found")
		return
	}

	messages, err := h.service.ListChannelMessages(ctx.Request.Context(), channelID)
	if err != nil {
		if errors.Is(err, ErrChannelNotFound) {
			httpresponse.NotFound(ctx, err.Error())
			return
		}

		logger.Error("failed to list channel messages", zap.Error(err))
		httpresponse.InternalServerError(ctx, "failed to list channel messages")
		return
	}

	httpresponse.JSON(ctx, http.StatusOK, ToMessageResponses(messages))
}
