package utils

import (
	"context"

	"go_websockets/internal/config"

	"go.uber.org/zap"
)

type loggerContextKey struct{}

var loggerKey = loggerContextKey{}

// NewLogger builds a zap logger configured for the given environment.
// Stack traces are limited to error level so expected control-flow warnings
// (e.g. "channel not found") don't dump a trace on every request.
func NewLogger(environment config.EnvironmentType) (*zap.Logger, error) {
	var cfg zap.Config
	if environment == config.Development {
		cfg = zap.NewDevelopmentConfig()
	} else {
		cfg = zap.NewProductionConfig()
	}

	return cfg.Build(zap.AddStacktrace(zap.ErrorLevel))
}

// WithLogger returns a new context carrying the given logger.
func WithLogger(ctx context.Context, logger *zap.Logger) context.Context {
	return context.WithValue(ctx, loggerKey, logger)
}

// LoggerFromContext extracts the logger from ctx, falling back to a no-op
// logger if none was set so callers never have to nil-check.
func LoggerFromContext(ctx context.Context) *zap.Logger {
	if logger, ok := ctx.Value(loggerKey).(*zap.Logger); ok {
		return logger
	}

	return zap.NewNop()
}
