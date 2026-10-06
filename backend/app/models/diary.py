from sqlalchemy import (Column, String, Integer,
                        Text, Boolean, ForeignKey)
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class DiaryEntry(BaseModel):
    """Запись дневника пользователя"""
    __tablename__ = "diary_entries"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)

    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    mood = Column(String(50), nullable=True)
    tags = Column(String(500), nullable=True)

    ai_summary = Column(Text, nullable=True)
    ai_insights = Column(Text, nullable=True)

    is_deleted = Column(Boolean, default=False)

    user = relationship(
        "User",
        back_populates="diary_entries",
    )

    dialogs = relationship(
        "DiaryDialog",
        foreign_keys="DiaryDialog.entry_id",
        back_populates="entry",
        cascade="all, delete-orphan",
    )

    messages = relationship(
        "DiaryMessage",
        foreign_keys="DiaryMessage.entry_id",
        back_populates="entry",
        cascade="all, delete-orphan",
    )