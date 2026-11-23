package channels

import "time"

type Channel struct {
	ID        int64     `gorm:"primaryKey"`
	Name      string    `gorm:"size:50;not null;index"`
	CreatedAt time.Time `gorm:"not null"`
}

func (Channel) TableName() string {
	return "channels"
}

type Message struct {
	ID        int64     `gorm:"primaryKey"`
	ChannelID int64     `gorm:"not null;index"`
	AuthorID  int64     `gorm:"not null"`
	Content   string    `gorm:"size:2000;not null"`
	CreatedAt time.Time `gorm:"not null"`
	EditedAt  *time.Time

	Channel Channel `gorm:"constraint:OnDelete:CASCADE;foreignKey:ChannelID;references:ID"`
}

func (Message) TableName() string {
	return "messages"
}
