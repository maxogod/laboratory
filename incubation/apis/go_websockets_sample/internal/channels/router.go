package channels

import "github.com/gin-gonic/gin"

// SetupChannelsRoutes registers the REST endpoints. service is built by the
// caller (internal/router) so the same instance can also be handed to the
// realtime package for the websocket endpoint.
func SetupChannelsRoutes(r *gin.Engine, service ChannelsService) error {
	channelsHandler := NewChannelsHandler(service)

	channelsGroup := r.Group("/channels")
	channelsGroup.POST("", channelsHandler.CreateChannel)
	channelsGroup.GET("", channelsHandler.GetChannelList)
	channelsGroup.GET("/:channelId/messages", channelsHandler.GetChannelMessages)

	return nil
}
