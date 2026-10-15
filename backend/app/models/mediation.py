from sqlalchemy import (Column, Integer, String, Text,
                        ForeignKey, Boolean, Enum, DateTime, UniqueConstraint)
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class MediationStatus(str, enum.Enum):
    """Статус сессии медиации (State Machine)."""
    PENDING = "pending"
    ACTIVE = "active"
    SUBMISSIONS_COMPLETE = "submissions_complete"
    AI_ANALYSIS = "ai_analysis"
    RESOLUTION_PROPOSED = "resolution_proposed"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class MediationSession(BaseModel):
    """Сессия ИИ-медиации между пользователями."""

    __tablename__ = "mediation_sessions"

    initiator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                          nullable=False, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                          nullable=False, index=True)

    status = Column(Enum(MediationStatus), default=MediationStatus.PENDING)
    topic = Column(String(200), nullable=True)

    initiator_submitted = Column(Boolean, default=False)
    recipient_submitted = Column(Boolean, default=False)

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


class GroupSessionStatus(str, enum.Enum):
    """Статус групповой сессии."""
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class GroupSession(BaseModel):
    """Групповая терапевтическая сессия."""

    __tablename__ = "group_sessions"

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    host_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer, default=60, nullable=False)
    max_participants = Column(Integer, default=10, nullable=False)

    status = Column(Enum(GroupSessionStatus), default=GroupSessionStatus.SCHEDULED)

    is_deleted = Column(Boolean, default=False)

    host = relationship("User", foreign_keys=[host_id])
    enrollments = relationship("GroupEnrollment", back_populates="session", cascade="all, delete-orphan")


class GroupEnrollment(BaseModel):
    """Запись пользователя на групповую сессию."""

    __tablename__ = "group_enrollments"

    session_id = Column(Integer, ForeignKey("group_sessions.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)

    enrolled_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint('session_id', 'user_id', name='uq_group_enrollment'),
    )

    session = relationship("GroupSession", back_populates="enrollments")
    user = relationship("User")