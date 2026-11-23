package realtime

import "github.com/gin-gonic/gin"

// SetupRoutes builds the Hub and registers the websocket upgrade endpoint.
// It returns the Hub so the caller can hold onto it for graceful shutdown
// (see App.Shutdown) — construction lives here, ownership lives with App.
func SetupRoutes(r *gin.Engine, service ChannelService, maxConnections, maxConnectionsPerChannel int) (*Hub, error) {
	hub := NewHub(maxConnections, maxConnectionsPerChannel)
	handler := NewHandler(service, hub)
	r.GET("/channels/:channelId/ws", handler.HandleConnection)

	return hub, nil
}
