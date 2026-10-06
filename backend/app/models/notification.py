from sqlalchemy import (Column, Integer, String, Text,
                        ForeignKey, Boolean, Enum, DateTime)
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class NotificationType(str, enum.Enum):
    """Тип уведомления."""
    CHAT_MESSAGE = "chat_message"
    MEDIATION_REQUEST = "mediation_request"
    MEDIATION_UPDATE = "mediation_update"
    SYSTEM = "system"


class Notification(BaseModel):
    """Уведомление пользователя."""

    __tablename__ = "notifications"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)

    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String(200), nullable=True)
    message = Column(Text, nullable=False)

    data = Column(Text, nullable=True)

    is_read = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    read_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="notifications")