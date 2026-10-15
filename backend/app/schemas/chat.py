from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class CreateChatRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=200,
                                description="Название чата (обязательно для групповых)")
    is_group: bool = Field(default=False, description="Является ли чат групповым")
    member_usernames: List[str] = Field(default_factory=list,
                                        description="Список username пользователей для приглашения")


class ChatMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    display_name: str
    role: str


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Optional[str]
    is_group: bool
    created_by_id: Optional[int]
    members: List[ChatMemberResponse]
    created_at: datetime


class CreateMessageRequest(BaseModel):
    content: Optional[str] = Field(None, max_length=4000,
                                   description="Текст сообщения (может быть пустым, если есть медиа)")
    media_attachment_id: Optional[int] = Field(None,
                                               description="ID медиафайла из Спринта 4 (опционально)")


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chat_id: int
    sender_id: int
    sender_username: str
    content: Optional[str]
    media_attachment_id: Optional[int]
    is_deleted: bool
    created_at: datetime
    edited_at: Optional[datetime]