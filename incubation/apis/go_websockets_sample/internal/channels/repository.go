package channels

import (
	"context"
	"errors"
	"time"

	"github.com/jackc/pgx/v5/pgconn"
	"gorm.io/gorm"
)

const (
	pgUniqueViolationCode     = "23505"
	pgForeignKeyViolationCode = "23503"
)

// Migrate creates/updates the channels and messages tables.
func Migrate(db *gorm.DB) error {
	if err := db.AutoMigrate(&Channel{}, &Message{}); err != nil {
		return err
	}

	return db.Exec(`CREATE UNIQUE INDEX IF NOT EXISTS idx_channels_name_lower ON channels (LOWER(name))`).Error
}

// PostgresChannelsRepository is a gorm-backed ChannelsRepository (see
// services.go, its consumer, for the interface it implements).
type PostgresChannelsRepository struct {
	db *gorm.DB
}

func NewPostgresChannelsRepository(db *gorm.DB) *PostgresChannelsRepository {
	return &PostgresChannelsRepository{db: db}
}

func (r *PostgresChannelsRepository) CreateChannel(ctx context.Context, name string) (*Channel, error) {
	channel := &Channel{Name: name, CreatedAt: now()}

	if err := r.db.WithContext(ctx).Create(channel).Error; err != nil {
		if isUniqueViolation(err) {
			return nil, ErrChannelNameExists
		}

		return nil, err
	}

	return channel, nil
}

func (r *PostgresChannelsRepository) ListChannels(ctx context.Context) ([]*Channel, error) {
	channels := make([]*Channel, 0)

	if err := r.db.WithContext(ctx).Order("created_at ASC").Find(&channels).Error; err != nil {
		return nil, err
	}

	return channels, nil
}

func (r *PostgresChannelsRepository) GetChannelByID(ctx context.Context, id int64) (*Channel, error) {
	var channel Channel

	if err := r.db.WithContext(ctx).First(&channel, id).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrChannelNotFound
		}

		return nil, err
	}

	return &channel, nil
}

func (r *PostgresChannelsRepository) ListMessagesByChannel(ctx context.Context, channelID int64) ([]*Message, error) {
	messages := make([]*Message, 0)

	if err := r.db.WithContext(ctx).
		Where("channel_id = ?", channelID).
		Order("created_at ASC, id ASC").
		Find(&messages).Error; err != nil {
		return nil, err
	}

	return messages, nil
}

func (r *PostgresChannelsRepository) CreateMessage(ctx context.Context, channelID, authorID int64, content string) (*Message, error) {
	message := &Message{
		ChannelID: channelID,
		AuthorID:  authorID,
		Content:   content,
		CreatedAt: now(),
	}

	if err := r.db.WithContext(ctx).Create(message).Error; err != nil {
		if isForeignKeyViolation(err) {
			return nil, ErrChannelNotFound
		}

		return nil, err
	}

	return message, nil
}

func (r *PostgresChannelsRepository) GetMessageByID(ctx context.Context, id int64) (*Message, error) {
	var message Message

	if err := r.db.WithContext(ctx).First(&message, id).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrMessageNotFound
		}

		return nil, err
	}

	return &message, nil
}

// UpdateMessageContent replaces a message's content and stamps editedAt.
// It re-reads the row afterwards rather than mutating the caller's struct
// in place, so the returned value always reflects what's actually stored.
func (r *PostgresChannelsRepository) UpdateMessageContent(ctx context.Context, id int64, content string) (*Message, error) {
	result := r.db.WithContext(ctx).Model(&Message{}).Where("id = ?", id).Updates(map[string]any{
		"content":   content,
		"edited_at": now(),
	})
	if result.Error != nil {
		return nil, result.Error
	}
	if result.RowsAffected == 0 {
		return nil, ErrMessageNotFound
	}

	return r.GetMessageByID(ctx, id)
}

// now truncates to microseconds, matching Postgres timestamptz precision
// (see the comment on Channel/Message in models.go).
func now() time.Time {
	return time.Now().UTC().Truncate(time.Microsecond)
}

func isUniqueViolation(err error) bool {
	var pgErr *pgconn.PgError
	return errors.As(err, &pgErr) && pgErr.Code == pgUniqueViolationCode
}

func isForeignKeyViolation(err error) bool {
	var pgErr *pgconn.PgError
	return errors.As(err, &pgErr) && pgErr.Code == pgForeignKeyViolationCode
}
