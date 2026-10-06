from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.chat import chat_members


class User(BaseModel):
    """Модель пользователя"""

    __tablename__ = 'users'

    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    display_name = Column(String(100), nullable=False)

    hashed_pin = Column(String(255), nullable=False)

    avatar_url = Column(String(500), nullable=True)

    consent_data_processing = Column(Boolean, default=False)
    consent_local_cache = Column(Boolean, default=False)
    consent_cloud_ai = Column(Boolean, default=False)

    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    diary_entries = relationship(
        "DiaryEntry",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    stabilization_dialogs = relationship(
        "DiaryDialog",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    chats = relationship(
        "Chat",
        secondary=chat_members,
        back_populates="members"
    )
    created_chats = relationship(
        "Chat",
        foreign_keys="Chat.created_by",
        back_populates="creator",
    )
    messages = relationship(
        "Message",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    mediation_initiated = relationship(
        "MediationSession",
        foreign_keys="MediationSession.initiator_id",
        back_populates="initiator"
    )
    mediation_received = relationship(
        "MediationSession",
        foreign_keys="MediationSession.recipient_id",
        back_populates="recipient"
    )
    mediation_consents = relationship(
        "MediationConsent",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    mediation_submissions = relationship(
        "MediationSubmission",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )