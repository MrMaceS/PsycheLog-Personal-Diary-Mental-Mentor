from sqlalchemy import (Column, String, Integer, Text, Boolean,
                        ForeignKey, DateTime)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta
from app.models.base import BaseModel


class MediaAttachment(BaseModel):
    """Медиафайл (аудио/видео) пользователя"""
    __tablename__ = "media_attachments"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)

    diary_entry_id = Column(Integer, ForeignKey("diary_entries.id", ondelete="SET NULL"),
                            nullable=True, index=True)

    media_type = Column(String(20), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    processing_status = Column(String(20), default="pending", nullable=False)
    transcription = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_file_deleted = Column(Boolean, default=False)

    user = relationship(
        "User",
        back_populates="media_attachments",
    )

    diary_entry = relationship(
        "DiaryEntry",
        back_populates="media_attachments",
    )

    def set_expiration(self, days: int = 7):
        """Устанавливает срок удаления файла"""
        self.expires_at = datetime.now(timezone.utc) + timedelta(days=days)

    @property
    def is_expired(self) -> bool:
        """Проверяет, истёк ли срок хранения файла"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at