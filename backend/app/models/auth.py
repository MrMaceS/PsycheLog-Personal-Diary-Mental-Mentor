from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class RefreshSession(BaseModel):
    __tablename__ = 'refresh_sessions'

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False)
    token_hash = Column(String(255), unique=True, index=True, nullable=False)
    device_info = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    #user = relationship("User", back_populates="refresh_sessions")


class OTPChallenge(BaseModel):
    __tablename__ = 'otp_challenges'

    email = Column(String(255), index=True, nullable=False)
    otp_hash = Column(String(255), nullable=False)
    purpose = Column(String(50), nullable=False) # "account_recovery", "email_verification"
    attempts = Column(Integer, default=0, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)