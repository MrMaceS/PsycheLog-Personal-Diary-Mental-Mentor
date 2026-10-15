from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.mediation import MediationStatus


class MediationRequestCreate(BaseModel):
    recipient_id: int = Field(..., description="ID пользователя, которому отправляется запрос")
    topic: Optional[str] = Field(None, max_length=200, description="Тема медиации")


class MediationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    initiator_id: int
    recipient_id: int
    status: MediationStatus
    topic: Optional[str]
    expires_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


class MediationRespondRequest(BaseModel):
    is_accepted: bool = Field(..., description="Принять или отклонить запрос")
    response_message: Optional[str] = Field(None, max_length=500, description="Комментарий к ответу")


class MediationSubmissionCreate(BaseModel):
    content: str = Field(..., min_length=10, max_length=5000, description="Позиция/аргумент")
    is_final: bool = Field(default=False, description="Это финальная позиция?")


class MediationSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    user_id: int
    content: str
    ai_analysis: Optional[str]
    is_final: bool
    created_at: datetime


class ConfirmResolutionRequest(BaseModel):
    is_confirmed: bool = Field(..., description="Подтвердить или отклонить AI-резюме")