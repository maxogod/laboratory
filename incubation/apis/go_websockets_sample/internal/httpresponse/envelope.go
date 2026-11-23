// Package httpresponse is the API's response contract: the {"data": ...}
// envelope for success and the problem+json ErrorResponse for failure
// (see error.go), shared by both REST handlers and the websocket protocol
// in internal/realtime so every response looks the same regardless of
// transport.
package httpresponse

import "github.com/gin-gonic/gin"

// Envelope is the {"data": ...} shape every successful response (HTTP or
// websocket) uses. Exported so callers outside of gin request handling
// (e.g. the realtime package, marshalling a frame to push over a
// websocket) can build the same shape without duplicating it.
type Envelope struct {
	Data any `json:"data"`
}

// New wraps data in the envelope without writing a response.
func New(data any) Envelope {
	return Envelope{Data: data}
}

// JSON writes data wrapped as {"data": data} with the given status code.
func JSON(ctx *gin.Context, status int, data any) {
	ctx.JSON(status, New(data))
}
