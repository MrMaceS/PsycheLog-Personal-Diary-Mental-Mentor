from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class TimestampMixin:
    """Миксин для добавления created_at и updated_at"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
                        nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now(), nullable=False)


class BaseModel(Base, TimestampMixin):
    """Базовая модель для всех таблиц"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)