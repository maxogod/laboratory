package httpresponse

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

const ProblemContentType = "application/problem+json"

// ErrorResponse is an RFC 7807-style problem body. It's shared verbatim by
// REST error responses (see Error below) and websocket error frames (see
// internal/realtime), so both transports report failures the same shape.
type ErrorResponse struct {
	Type     string `json:"type"`
	Title    string `json:"title"`
	Status   int    `json:"status"`
	Detail   string `json:"detail"`
	Instance string `json:"instance"`
}

// Error aborts the request with a problem+json body describing the error.
func Error(ctx *gin.Context, status int, title, detail string) {
	ctx.Header("Content-Type", ProblemContentType)
	ctx.AbortWithStatusJSON(status, ErrorResponse{
		Type:     "about:blank",
		Title:    title,
		Status:   status,
		Detail:   detail,
		Instance: ctx.Request.URL.Path,
	})
}

func BadRequest(ctx *gin.Context, detail string) {
	Error(ctx, http.StatusBadRequest, "Bad Request", detail)
}

func NotFound(ctx *gin.Context, detail string) {
	Error(ctx, http.StatusNotFound, "Not Found", detail)
}

func Forbidden(ctx *gin.Context, detail string) {
	Error(ctx, http.StatusForbidden, "Forbidden", detail)
}

func InternalServerError(ctx *gin.Context, detail string) {
	Error(ctx, http.StatusInternalServerError, "Internal Server Error", detail)
}

func ServiceUnavailable(ctx *gin.Context, detail string) {
	Error(ctx, http.StatusServiceUnavailable, "Service Unavailable", detail)
}
