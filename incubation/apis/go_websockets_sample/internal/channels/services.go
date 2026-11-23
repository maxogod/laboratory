package channels

import (
	"context"
	"errors"
	"strings"
	"unicode/utf8"

	"go_websockets/internal/utils"

	"go.uber.org/zap"
)

// ChannelsRepository is the persistence contract the service depends on.
// Declared here, on the consumer side, rather than next to its
// implementation in repository.go.
type ChannelsRepository interface {
	CreateChannel(ctx context.Context, name string) (*Channel, error)
	ListChannels(ctx context.Context) ([]*Channel, error)
	GetChannelByID(ctx context.Context, id int64) (*Channel, error)
	ListMessagesByChannel(ctx context.Context, channelID int64) ([]*Message, error)
	CreateMessage(ctx context.Context, channelID, authorID int64, content string) (*Message, error)
	GetMessageByID(ctx context.Context, id int64) (*Message, error)
	UpdateMessageContent(ctx context.Context, id int64, content string) (*Message, error)
}

const maxMessageContentLength = 2000

// channelsService implements the ChannelsService interface declared by its
// consumer in handlers.go.
type channelsService struct {
	repo ChannelsRepository
}

func NewChannelsService(repo ChannelsRepository) *channelsService {
	return &channelsService{repo: repo}
}

func (s *channelsService) CreateChannel(ctx context.Context, name string) (*Channel, error) {
	logger := utils.LoggerFromContext(ctx)

	name = strings.TrimSpace(name)
	if name == "" || !isValidText(name) {
		return nil, ErrInvalidChannelName
	}

	channel, err := s.repo.CreateChannel(ctx, name)
	if err != nil {
		if errors.Is(err, ErrChannelNameExists) {
			logger.Warn("channel name already exists", zap.String("name", name))
			return nil, err
		}

		logger.Error("failed to create channel", zap.Error(err))
		return nil, err
	}

	logger.Info("channel created", zap.Int64("channel_id", channel.ID))

	return channel, nil
}

func (s *channelsService) ListChannels(ctx context.Context) ([]*Channel, error) {
	channels, err := s.repo.ListChannels(ctx)
	if err != nil {
		utils.LoggerFromContext(ctx).Error("failed to list channels", zap.Error(err))
		return nil, err
	}

	return channels, nil
}

func (s *channelsService) ListChannelMessages(ctx context.Context, channelID int64) ([]*Message, error) {
	logger := utils.LoggerFromContext(ctx)

	if _, err := s.repo.GetChannelByID(ctx, channelID); err != nil {
		if errors.Is(err, ErrChannelNotFound) {
			logger.Warn("channel not found", zap.Int64("channel_id", channelID))
			return nil, err
		}

		logger.Error("failed to fetch channel", zap.Error(err))
		return nil, err
	}

	messages, err := s.repo.ListMessagesByChannel(ctx, channelID)
	if err != nil {
		logger.Error("failed to list channel messages", zap.Error(err))
		return nil, err
	}

	return messages, nil
}

// GetChannel is used by the websocket handler to verify a channel exists
// before upgrading the connection.
func (s *channelsService) GetChannel(ctx context.Context, channelID int64) (*Channel, error) {
	logger := utils.LoggerFromContext(ctx)

	channel, err := s.repo.GetChannelByID(ctx, channelID)
	if err != nil {
		if errors.Is(err, ErrChannelNotFound) {
			logger.Warn("channel not found", zap.Int64("channel_id", channelID))
			return nil, err
		}

		logger.Error("failed to fetch channel", zap.Error(err))
		return nil, err
	}

	return channel, nil
}

// SendMessage creates a new message in a channel. Called from the
// websocket handler when a SendOrEditMessageEvent omits id.
func (s *channelsService) SendMessage(ctx context.Context, channelID, authorID int64, content string) (*Message, error) {
	logger := utils.LoggerFromContext(ctx)

	content = strings.TrimSpace(content)
	if content == "" || utf8.RuneCountInString(content) > maxMessageContentLength || !isValidText(content) {
		return nil, ErrInvalidMessageContent
	}

	message, err := s.repo.CreateMessage(ctx, channelID, authorID, content)
	if err != nil {
		if errors.Is(err, ErrChannelNotFound) {
			logger.Warn("cannot send message to missing channel")
			return nil, err
		}

		logger.Error("failed to create message", zap.Error(err))
		return nil, err
	}

	logger.Info("message created", zap.Int64("message_id", message.ID))

	return message, nil
}

// EditMessage replaces an existing message's content. Called from the
// websocket handler when a SendOrEditMessageEvent includes id; authorID
// must match the message's original author.
func (s *channelsService) EditMessage(ctx context.Context, channelID, messageID, authorID int64, content string) (*Message, error) {
	logger := utils.LoggerFromContext(ctx)

	content = strings.TrimSpace(content)
	if content == "" || utf8.RuneCountInString(content) > maxMessageContentLength || !isValidText(content) {
		return nil, ErrInvalidMessageContent
	}

	existing, err := s.repo.GetMessageByID(ctx, messageID)
	if err != nil {
		if errors.Is(err, ErrMessageNotFound) {
			logger.Warn("message not found", zap.Int64("message_id", messageID))
			return nil, err
		}

		logger.Error("failed to fetch message", zap.Error(err))
		return nil, err
	}

	if existing.ChannelID != channelID {
		// Don't reveal that the message exists in a different channel.
		logger.Warn("message does not belong to channel",
			zap.Int64("message_id", messageID), zap.Int64("actual_channel_id", existing.ChannelID))
		return nil, ErrMessageNotFound
	}

	if existing.AuthorID != authorID {
		logger.Warn("author mismatch on message edit", zap.Int64("message_id", messageID))
		return nil, ErrMessageAuthorMismatch
	}

	updated, err := s.repo.UpdateMessageContent(ctx, messageID, content)
	if err != nil {
		logger.Error("failed to update message", zap.Error(err))
		return nil, err
	}

	logger.Info("message edited", zap.Int64("message_id", messageID))

	return updated, nil
}

// isValidText rejects NUL bytes and invalid UTF-8 — both valid to receive
// over JSON, but Postgres text columns refuse to store them. Better to
// reject as a 400 here than let a raw driver error surface as a 500.
func isValidText(s string) bool {
	return utf8.ValidString(s) && !strings.ContainsRune(s, 0)
}
