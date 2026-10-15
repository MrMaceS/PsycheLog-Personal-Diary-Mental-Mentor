from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.mediation import GroupSessionStatus


class GroupSessionCreate(BaseModel):
    title: str = Field(..., max_length=200, description="Название сессии")
    description: Optional[str] = Field(None, max_length=2000, description="Описание сессии")
    scheduled_at: datetime = Field(..., description="Дата и время начала сессии (UTC)")
    duration_minutes: int = Field(default=60, ge=15, le=180, description="Длительность в минутах")
    max_participants: int = Field(default=10, ge=2, le=50, description="Максимальное количество участников")


class GroupSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    host_id: Optional[int]
    scheduled_at: datetime
    duration_minutes: int
    max_participants: int
    status: GroupSessionStatus
    created_at: datetime
    enrolled_count: int = Field(default=0, description="Количество записавшихся участников")


class GroupEnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    user_id: int
    enrolled_at: datetime