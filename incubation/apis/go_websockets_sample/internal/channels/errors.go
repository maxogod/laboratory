package channels

import "errors"

var (
	ErrChannelNotFound    = errors.New("channel not found")
	ErrChannelNameExists  = errors.New("channel name already exists")
	ErrInvalidChannelName = errors.New("channel name must not be blank")

	ErrMessageNotFound       = errors.New("message not found")
	ErrMessageAuthorMismatch = errors.New("author does not match the message's original author")
	ErrInvalidMessageContent = errors.New("message content must be between 1 and 2000 characters")
)
