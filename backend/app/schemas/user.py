from datetime import datetime
from typing import Optional
from app.core.security import verify_pin
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    display_name: str
    avatar_url: Optional[str] = None

    consent_data_processing: bool
    consent_local_cache: bool
    consent_cloud_ai: bool

    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class UpdateUserRequest(BaseModel):
    display_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    avatar_url: Optional[str] = Field(
        default=None,
        max_length=500,
    )


class UpdateConsentsRequest(BaseModel):
    consent_data_processing: Optional[bool] = None
    consent_local_cache: Optional[bool] = None
    consent_cloud_ai: Optional[bool] = None


class DeleteAccountRequest(BaseModel):
    pin: str = Field(
        min_length=4,
        max_length=20,
    )