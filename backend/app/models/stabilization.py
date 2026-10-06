from sqlalchemy import (Column, Integer, String, Text,
                        ForeignKey, Boolean, Enum, DateTime)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.base import BaseModel


class DialogStatus(str, enum.Enum):
    """Статус сессии стабилизации."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class DiaryDialog(BaseModel):
    """Сессия диалога стабилизации."""
    __tablename__ = "diary_dialogs"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    entry_id = Column(Integer, ForeignKey("diary_entries.id", ondelete="CASCADE"),
                      nullable=True, index=True)

    status = Column(Enum(DialogStatus), default=DialogStatus.ACTIVE)
    trigger = Column(String(100), nullable=True)

    ai_summary = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)

    is_deleted = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship(
        "User",
        back_populates="stabilization_dialogs",
    )

    entry = relationship(
        "DiaryEntry",
        foreign_keys=[entry_id],
        back_populates="dialogs",
    )

    messages = relationship(
        "DiaryMessage",
        foreign_keys="DiaryMessage.dialog_id",
        back_populates="dialog",
        cascade="all, delete-orphan",
    )


class DiaryMessage(BaseModel):
    """Сообщение в сессии стабилизации."""

    __tablename__ = "diary_messages"

    dialog_id = Column(
        Integer,
        ForeignKey("diary_dialogs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    entry_id = Column(
        Integer,
        ForeignKey("diary_entries.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)

    dialog = relationship(
        "DiaryDialog",
        foreign_keys=[dialog_id],
        back_populates="messages",
    )

    entry = relationship(
        "DiaryEntry",
        foreign_keys=[entry_id],
        back_populates="messages",
    )