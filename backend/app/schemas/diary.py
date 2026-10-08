from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class CreateDiaryEntry(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: str
    mood: Optional[str] = Field(None, max_length=50)
    tags: Optional[str] = Field(None, max_length=500)


class UpdateDiaryEntry(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(default=None)
    mood: Optional[str] = Field(None, max_length=50)
    tags: Optional[str] = Field(None, max_length=500)


class DiaryEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: Optional[str]
    content: str
    mood: Optional[str]
    tags: Optional[str]
    ai_summary: Optional[str]
    ai_insights: Optional[str]
    is_deleted: bool
    created_at: datetime
    updated_at: datetime