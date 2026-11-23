package router

import (
	"go_websockets/internal/channels"
	"go_websockets/internal/config"
	"go_websockets/internal/realtime"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

// SetupRouter builds one channels service backed by db and wires it into
// both the REST routes and the websocket upgrade route, so REST reads/
// writes and websocket-driven message events go through the same business
// logic and land in the same database. It returns the realtime Hub so the
// caller can hold onto it for graceful shutdown.
func SetupRouter(r *gin.Engine, db *gorm.DB, cfg *config.Config) (*realtime.Hub, error) {
	repo := channels.NewPostgresChannelsRepository(db)
	service := channels.NewChannelsService(repo)

	if err := channels.SetupChannelsRoutes(r, service); err != nil {
		return nil, err
	}

	hub, err := realtime.SetupRoutes(r, service, cfg.WSMaxConnections, cfg.WSMaxConnectionsPerChannel)
	if err != nil {
		return nil, err
	}

	return hub, nil
}
