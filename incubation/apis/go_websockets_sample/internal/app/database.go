package app

import (
	"fmt"

	"go_websockets/internal/channels"
	"go_websockets/internal/config"
	"go_websockets/internal/utils"

	"go.uber.org/zap"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// connectDatabase opens the Postgres connection and runs migrations.
func connectDatabase(cfg *config.Config, logger *zap.Logger) (*gorm.DB, error) {
	db, err := gorm.Open(postgres.Open(cfg.DatabaseURL), &gorm.Config{
		Logger: utils.NewGormZapLogger(logger),
	})
	if err != nil {
		return nil, fmt.Errorf("connect to database: %w", err)
	}

	if err := channels.Migrate(db); err != nil {
		return nil, fmt.Errorf("migrate database: %w", err)
	}

	return db, nil
}
