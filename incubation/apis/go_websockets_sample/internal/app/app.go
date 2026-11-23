package app

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"go_websockets/internal/config"
	"go_websockets/internal/middlewares"
	"go_websockets/internal/realtime"
	"go_websockets/internal/router"
	"go_websockets/internal/utils"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
	"gorm.io/gorm"
)

const shutdownTimeout = 5 * time.Second

type App struct {
	config *config.Config
	logger *zap.Logger
	db     *gorm.DB
	hub    *realtime.Hub
	server *http.Server
}

func NewApp(config *config.Config) (*App, error) {
	logger, err := utils.NewLogger(config.Environment)
	if err != nil {
		return nil, err
	}

	return &App{
		config: config,
		logger: logger,
	}, nil
}

func (a *App) Start() error {
	switch a.config.Environment {
	case config.Development:
		gin.SetMode(gin.DebugMode)
	default:
		gin.SetMode(gin.ReleaseMode)
	}

	db, err := connectDatabase(a.config, a.logger)
	if err != nil {
		a.logger.Error("failed to initialize database", zap.Error(err))
		return err
	}
	a.db = db

	r := gin.Default()
	r.Use(middlewares.LoggerContext(a.logger))

	hub, err := router.SetupRouter(r, a.db, a.config)
	if err != nil {
		return err
	}
	a.hub = hub

	a.server = &http.Server{
		Addr:    fmt.Sprintf("%s:%d", a.config.Host, a.config.Port),
		Handler: r,
	}

	a.logger.Info("starting server", zap.String("addr", a.server.Addr))

	if err := a.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		a.logger.Error("server error", zap.Error(err))
		return err
	}

	return nil
}

func (a *App) Shutdown() error {
	ctx, cancel := context.WithTimeout(context.Background(), shutdownTimeout)
	defer cancel()

	defer func() {
		_ = a.logger.Sync()
	}()

	// http.Server.Shutdown below does not wait for or close hijacked
	// connections like websockets, so we drain them ourselves first,
	// bounded by the same deadline as the rest of this shutdown.
	if a.hub != nil {
		if !a.hub.Shutdown(ctx) {
			a.logger.Warn("timed out waiting for websocket connections to close")
		}
	}

	if a.db != nil {
		if sqlDB, err := a.db.DB(); err != nil {
			a.logger.Error("failed to get underlying sql.DB", zap.Error(err))
		} else if err := sqlDB.Close(); err != nil {
			a.logger.Error("error closing database connection", zap.Error(err))
		} else {
			a.logger.Info("database connection closed")
		}
	}

	if err := a.server.Shutdown(ctx); err != nil {
		a.logger.Error("server forced to shutdown", zap.Error(err))
		return err
	}

	a.logger.Info("server exited properly")

	return nil
}
