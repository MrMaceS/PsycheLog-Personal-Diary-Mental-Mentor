import enum
from sqlalchemy import (Column, Integer, String, Text, ForeignKey,
                        Boolean, Table, DateTime)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import BaseModel


class ChatRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


chat_members = Table(
    "chat_members",
    BaseModel.metadata,
    Column("chat_id", Integer, ForeignKey("chats.id", ondelete="CASCADE"),
           primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"),
           primary_key=True),
    Column("role", String(50), default="member"),
    Column("joined_at", DateTime(timezone=True), server_default=func.now()),
)


class Chat(BaseModel):
    """Чат (личный или групповой)."""

    __tablename__ = "chats"

    name = Column(String(200), nullable=True)
    is_group = Column(Boolean, default=False)
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    is_deleted = Column(Boolean, default=False)

    creator = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_chats",
    )
    members = relationship(
        "User",
        secondary=chat_members,
        back_populates="chats"
    )
    messages = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan"
    )


class Message(BaseModel):
    """Сообщение в чате."""

    __tablename__ = "messages"

    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)

    content = Column(Text, nullable=True)

    media_attachment_id = Column(
        Integer,
        ForeignKey("media_attachments.id", ondelete="SET NULL"),
        nullable=True
    )

    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    deleted_by_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    edited_at = Column(DateTime(timezone=True), nullable=True)

    chat = relationship("Chat", back_populates="messages")
    user = relationship("User", foreign_keys=[user_id], back_populates="messages")
    deleted_by = relationship("User", foreign_keys=[deleted_by_id])
    media_attachment = relationship("MediaAttachment")