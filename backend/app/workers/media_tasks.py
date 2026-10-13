import asyncio
from sqlalchemy import select
from app.workers.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.media import MediaAttachment
from app.core.logging_config import get_logger
from app.services.storage_service import storage_service
from datetime import datetime, timezone
logger = get_logger(__name__)


@celery_app.task(
    name="app.workers.media_tasks.transcribe_media_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def transcribe_media_task(self, media_id: int):
    """
    Асинхронная транскрибация медиафайла.
    1. Проверяет статус в БД.
    2. Имитирует скачивание и обработку Whisper (здесь будет реальный вызов API).
    3. Сохраняет текст и меняет статус на 'completed' или 'failed'.
    """

    async def _process():
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(MediaAttachment).where(MediaAttachment.id == media_id)
                )
                media = result.scalar_one_or_none()

                if not media:
                    logger.warning("transcribe_media_task_failed: media not found", media_id=media_id)
                    return

                if media.processing_status != "transcribing":
                    logger.info(
                        "transcribe_media_task_skipped: status changed",
                        media_id=media_id,
                        status=media.processing_status,
                    )
                    return

                # Имитация скачивания и транскрибации (Whisper)
                # В продакшене здесь будет:
                # file_obj = storage_service.s3_client.get_object(Bucket=..., Key=media.file_path)
                # result = whisper_model.transcribe(file_obj['Body'].read())
                # transcription_text = result['text']

                await asyncio.sleep(2)

                transcription_text = (
                    f"[Транскрибация аудио #{media.id}]: "
                    "Пользователь описывает свой день, упоминает рабочие задачи и легкую усталость. "
                    "Настроение в целом спокойное, но присутствует легкая тревога о будущем."
                )

                media.transcription = transcription_text
                media.processing_status = "completed"

                await db.commit()

                logger.info(
                    "transcribe_media_task_completed",
                    media_id=media_id,
                    transcription_length=len(transcription_text),
                )

            except Exception as e:
                await db.rollback()
                logger.error(
                    "transcribe_media_task_failed",
                    media_id=media_id,
                    error=str(e),
                )

                raise self.retry(exc=e)

    try:
        asyncio.run(_process())
    except Exception as e:
        logger.error(
            "transcribe_media_task_asyncio_failed",
            media_id=media_id,
            error=str(e),
        )
        raise self.retry(exc=e)


@celery_app.task(
    name="app.workers.media_tasks.cleanup_expired_media_task",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 минут
)
def cleanup_expired_media_task(self):
    """
    Периодическая задача: удаляет просроченные медиафайлы из MinIO.
    Транскрипция остаётся в БД, но сам файл удаляется.
    """

    async def _cleanup():
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(MediaAttachment).where(
                        MediaAttachment.is_file_deleted == False,
                        MediaAttachment.expires_at < datetime.now(timezone.utc),
                    )
                )
                expired_media = result.scalars().all()

                if not expired_media:
                    logger.info("cleanup_expired_media_task: no expired media found")
                    return

                deleted_count = 0
                failed_count = 0

                for media in expired_media:
                    try:
                        storage_service.delete_file(media.file_path)

                        media.is_file_deleted = True
                        deleted_count += 1

                        logger.info(
                            "media_file_deleted",
                            media_id=media.id,
                            file_path=media.file_path,
                        )

                    except Exception as e:
                        logger.error(
                            "media_file_deletion_failed",
                            media_id=media.id,
                            error=str(e),
                        )
                        failed_count += 1

                await db.commit()

                logger.info(
                    "cleanup_expired_media_task_completed",
                    deleted=deleted_count,
                    failed=failed_count,
                )

            except Exception as e:
                await db.rollback()
                logger.error("cleanup_expired_media_task_failed", error=str(e))
                raise self.retry(exc=e)

    try:
        asyncio.run(_cleanup())
    except Exception as e:
        logger.error("cleanup_expired_media_task_asyncio_failed", error=str(e))
        raise self.retry(exc=e)