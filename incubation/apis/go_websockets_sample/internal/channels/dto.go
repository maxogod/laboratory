package channels

import "time"

// CreateChannelRequest is the request body for POST /channels.
type CreateChannelRequest struct {
	Name string `json:"name" binding:"required,min=1,max=50"`
}

// ChannelResponse is the API representation of a Channel.
type ChannelResponse struct {
	ID        int64     `json:"id"`
	Name      string    `json:"name"`
	CreatedAt time.Time `json:"createdAt"`
}

func ToChannelResponse(c *Channel) ChannelResponse {
	return ChannelResponse{ID: c.ID, Name: c.Name, CreatedAt: c.CreatedAt}
}

func ToChannelResponses(channels []*Channel) []ChannelResponse {
	responses := make([]ChannelResponse, len(channels))
	for i, c := range channels {
		responses[i] = ToChannelResponse(c)
	}

	return responses
}

// MessageResponse is the API representation of a Message.
type MessageResponse struct {
	ID        int64      `json:"id"`
	ChannelID int64      `json:"channelId"`
	AuthorID  int64      `json:"authorId"`
	Content   string     `json:"content"`
	CreatedAt time.Time  `json:"createdAt"`
	EditedAt  *time.Time `json:"editedAt"`
}

func ToMessageResponse(m *Message) MessageResponse {
	return MessageResponse{
		ID:        m.ID,
		ChannelID: m.ChannelID,
		AuthorID:  m.AuthorID,
		Content:   m.Content,
		CreatedAt: m.CreatedAt,
		EditedAt:  m.EditedAt,
	}
}

func ToMessageResponses(messages []*Message) []MessageResponse {
	responses := make([]MessageResponse, len(messages))
	for i, m := range messages {
		responses[i] = ToMessageResponse(m)
	}

	return responses
}
