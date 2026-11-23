package utils

import (
	"context"
	"errors"
	"time"

	"go.uber.org/zap"
	gormlogger "gorm.io/gorm/logger"
)

const slowQueryThreshold = 200 * time.Millisecond

// GormZapLogger routes gorm's query/error logging through zap instead of
// gorm's default stdlib logger, so SQL-level logs share the app's format
// and, for queries run with db.WithContext(ctx), pick up the same
// request-scoped fields (method, path, client_ip) the HTTP logs have.
type GormZapLogger struct {
	base *zap.Logger
}

// NewGormZapLogger builds a gorm logger.Interface backed by base, used as
// the fallback when a query isn't running against a request context (e.g.
// migrations at startup).
func NewGormZapLogger(base *zap.Logger) *GormZapLogger {
	return &GormZapLogger{base: base}
}

func (l *GormZapLogger) LogMode(gormlogger.LogLevel) gormlogger.Interface {
	return l
}

func (l *GormZapLogger) Info(ctx context.Context, msg string, args ...any) {
	l.loggerFor(ctx).Sugar().Infof(msg, args...)
}

func (l *GormZapLogger) Warn(ctx context.Context, msg string, args ...any) {
	l.loggerFor(ctx).Sugar().Warnf(msg, args...)
}

func (l *GormZapLogger) Error(ctx context.Context, msg string, args ...any) {
	l.loggerFor(ctx).Sugar().Errorf(msg, args...)
}

func (l *GormZapLogger) Trace(ctx context.Context, begin time.Time, fc func() (string, int64), err error) {
	logger := l.loggerFor(ctx)
	elapsed := time.Since(begin)
	sql, rows := fc()

	fields := []zap.Field{
		zap.String("sql", sql),
		zap.Int64("rows", rows),
		zap.Duration("elapsed", elapsed),
	}

	switch {
	case err != nil && !errors.Is(err, gormlogger.ErrRecordNotFound):
		logger.Error("gorm query failed", append(fields, zap.Error(err))...)
	case elapsed > slowQueryThreshold:
		logger.Warn("slow gorm query", fields...)
	default:
		logger.Debug("gorm query", fields...)
	}
}

// loggerFor prefers the request-scoped logger set by middlewares.LoggerContext,
// falling back to the base app logger for queries with no request context
// (startup migrations, background jobs) instead of LoggerFromContext's Nop.
func (l *GormZapLogger) loggerFor(ctx context.Context) *zap.Logger {
	if logger, ok := ctx.Value(loggerKey).(*zap.Logger); ok {
		return logger
	}

	return l.base
}
