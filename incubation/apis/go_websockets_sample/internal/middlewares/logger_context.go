package middlewares

import (
	"go_websockets/internal/utils"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// LoggerContext injects a request-scoped zap logger into the request context
// so it's reachable from any handler via utils.LoggerFromContext(ctx.Request.Context()).
func LoggerContext(logger *zap.Logger) gin.HandlerFunc {
	return func(ctx *gin.Context) {
		requestLogger := logger.With(
			zap.String("method", ctx.Request.Method),
			zap.String("path", ctx.Request.URL.Path),
			zap.String("client_ip", ctx.ClientIP()),
		)

		ctx.Request = ctx.Request.WithContext(utils.WithLogger(ctx.Request.Context(), requestLogger))

		ctx.Next()
	}
}
