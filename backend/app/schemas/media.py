from pydantic import BaseModel, Field
from typing import Optional


class RequestUploadRequest(BaseModel):
    file_name: str = Field(..., description="Имя файла, например, 'voice_note.mp3'")
    content_type: str = Field(..., description="MIME-тип, например, 'audio/mpeg'")
    media_type: str = Field(..., description="'audio' или 'video'")
    diary_entry_id: Optional[int] = Field(None, description="ID записи дневника, если медиа к ней привязано")


class RequestUploadResponse(BaseModel):
    media_id: int
    presigned_url: str
    file_path: str


class ConfirmUploadResponse(BaseModel):
    media_id: int
    status: str
    message: str = "Загрузка подтверждена, началась транскрибация"