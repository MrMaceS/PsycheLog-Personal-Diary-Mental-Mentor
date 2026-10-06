from sqlalchemy import (Column, Integer, String, Text,
                        ForeignKey, Boolean, Enum, DateTime)
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class MediationStatus(str, enum.Enum):
    """Статус сессии медиации."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    DECLINED = "declined"
    EXPIRED = "expired"


class MediationSession(BaseModel):
    """Сессия ИИ-медиации между пользователями."""

    __tablename__ = "mediation_sessions"

    initiator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                          nullable=False, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                          nullable=False, index=True)

    status = Column(Enum(MediationStatus), default=MediationStatus.PENDING)
    topic = Column(String(200), nullable=True)

    ai_summary = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)

    expires_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    is_deleted = Column(Boolean, default=False)

    initiator = relationship("User", foreign_keys=[initiator_id],
                             back_populates="mediation_initiated")
    recipient = relationship("User", foreign_keys=[recipient_id],
                             back_populates="mediation_received")
    consents = relationship("MediationConsent", back_populates="session",
                            cascade="all, delete-orphan")
    submissions = relationship("MediationSubmission", back_populates="session",
                               cascade="all, delete-orphan")


class MediationConsent(BaseModel):
    """Согласие пользователя на участие в медиации."""

    __tablename__ = "mediation_consents"

    session_id = Column(Integer, ForeignKey("mediation_sessions.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)

    is_accepted = Column(Boolean, nullable=True)
    response_message = Column(Text, nullable=True)

    responded_at = Column(DateTime(timezone=True), nullable=True)

    session = relationship("MediationSession", back_populates="consents")
    user = relationship("User", back_populates="mediation_consents")


class MediationSubmission(BaseModel):
    """Позиция/аргумент пользователя в медиации."""

    __tablename__ = "mediation_submissions"

    session_id = Column(Integer, ForeignKey("mediation_sessions.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)

    content = Column(Text, nullable=False)
    ai_analysis = Column(Text, nullable=True)

    is_final = Column(Boolean, default=False)

    session = relationship("MediationSession", back_populates="submissions")
    user = relationship("User", back_populates="mediation_submissions")