import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.logging_config import get_logger
from app.models.user import User
from app.models.media import MediaAttachment
from app.schemas.media import (
    RequestUploadRequest,
    RequestUploadResponse,
    ConfirmUploadResponse,
)
from app.services.storage_service import storage_service
from app.api.v1.diary import get_current_user
from app.workers.media_tasks import transcribe_media_task, cleanup_expired_media_task
from sqlalchemy import select

logger = get_logger(__name__)
router = APIRouter(prefix="/media", tags=["Media"])


@router.post("/request-upload", response_model=RequestUploadResponse)
async def request_upload(
    request: RequestUploadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Шаг 1: Получение presigned URL для прямой загрузки файла в MinIO.
    Создает запись в БД со статусом 'pending'.
    """
    if not current_user.consent_data_processing:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Загрузка медиа недоступна. Вы отозвали согласие на обработку данных.",
        )

    if request.media_type == "audio" and not current_user.consent_cloud_ai:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Загрузка аудио недоступна. Вы отозвали согласие на облачный AI.",
        )

    file_extension = request.file_name.split(".")[-1] if "." in request.file_name else "bin"
    unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
    file_path = f"users/{current_user.id}/media/{unique_filename}"

    presigned_url = storage_service.generate_presigned_upload_url(
        object_name=file_path,
        content_type=request.content_type,
    )

    media = MediaAttachment(
        user_id=current_user.id,
        diary_entry_id=request.diary_entry_id,
        media_type=request.media_type,
        mime_type=request.content_type,
        file_path=file_path,
        processing_status="pending",
    )
    media.set_expiration(days=7)

    db.add(media)
    await db.commit()
    await db.refresh(media)

    logger.info(
        "media_upload_requested",
        media_id=media.id,
        user_id=current_user.id,
    )

    return RequestUploadResponse(
        media_id=media.id,
        presigned_url=presigned_url,
        file_path=file_path,
    )


@router.post("/{media_id}/confirm", response_model=ConfirmUploadResponse)
async def confirm_upload(
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Шаг 2: Подтверждение загрузки.
    Фронтенд вызывает этот эндпоинт после успешного PUT-запроса в MinIO.
    Запускает Celery-задачу для транскрибации.
    """
    result = await db.execute(
        select(MediaAttachment).where(
            MediaAttachment.id == media_id,
            MediaAttachment.user_id == current_user.id,
        )
    )
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Медиафайл не найден или не принадлежит пользователю",
        )

    if media.processing_status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неверный статус медиа: {media.processing_status}",
        )

    media.processing_status = "transcribing"
    await db.commit()

    transcribe_media_task.delay(media.id)

    logger.info(
        "media_upload_confirmed",
        media_id=media.id,
        user_id=current_user.id,
    )

    return ConfirmUploadResponse(
        media_id=media.id,
        status=media.processing_status,
    )


@router.post("/cleanup-expired")
async def manual_cleanup_expired_media(
        current_user: User = Depends(get_current_user),
):
    """
    Ручной запуск задачи очистки просроченных медиа.
    Только для администраторов/тестирования.
    """

    task = cleanup_expired_media_task.delay()

    return {
        "message": "Задача очистки запущена",
        "task_id": task.id,
    }


@router.get("/{media_id}")
async def get_media_status(
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Получение статуса медиафайла и транскрипции (если готова).
    """
    result = await db.execute(
        select(MediaAttachment).where(
            MediaAttachment.id == media_id,
            MediaAttachment.user_id == current_user.id,
        )
    )
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Медиафайл не найден или не принадлежит пользователю",
        )

    return {
        "media_id": media.id,
        "status": media.processing_status,
        "transcription": media.transcription,
        "is_file_deleted": media.is_file_deleted,
        "created_at": media.created_at.isoformat(),
        "expires_at": media.expires_at.isoformat() if media.expires_at else None,
    }


@router.get("/")
async def list_user_media(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Список всех медиафайлов пользователя.
    """
    result = await db.execute(
        select(MediaAttachment)
        .where(MediaAttachment.user_id == current_user.id)
        .order_by(MediaAttachment.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    media_list = result.scalars().all()

    return [
        {
            "media_id": media.id,
            "media_type": media.media_type,
            "status": media.processing_status,
            "has_transcription": media.transcription is not None,
            "created_at": media.created_at.isoformat(),
        }
        for media in media_list
    ]