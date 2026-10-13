from datetime import datetime, timezone
from sqlalchemy import delete, select
from app.workers.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.diary import DiaryEntry
from app.models.chat import Message
from app.models.mediation import MediationConsent, MediationSubmission
from app.models.notification import Notification
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@celery_app.task(
    name="app.workers.account_cleanup_tasks.cleanup_deleted_account",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def cleanup_deleted_account(self, user_id: int):
    """
    Асинхронная очистка всех данных удалённого пользователя.
    Запускается после soft delete аккаунта.
    """
    import asyncio

    async def _cleanup():
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()

                if not user or not user.is_deleted:
                    logger.warning(
                        "cleanup_skipped_user_not_deleted",
                        user_id=user_id,
                    )
                    return

                await db.execute(
                    delete(DiaryEntry).where(DiaryEntry.user_id == user_id)
                )

                await db.execute(
                    delete(Message).where(Message.user_id == user_id)
                )

                await db.execute(
                    delete(MediationConsent).where(MediationConsent.user_id == user_id)
                )

                await db.execute(
                    delete(MediationSubmission).where(MediationSubmission.user_id == user_id)
                )

                await db.execute(
                    delete(Notification).where(Notification.user_id == user_id)
                )

                await db.commit()

                logger.info(
                    "account_data_cleaned",
                    user_id=user_id,
                )

            except Exception as e:
                logger.error(
                    "account_cleanup_failed",
                    user_id=user_id,
                    error=str(e),
                )
                await db.rollback()
                raise

    try:
        asyncio.run(_cleanup())
    except Exception as e:
        logger.error(
            "account_cleanup_task_failed",
            user_id=user_id,
            error=str(e),
        )

        raise self.retry(exc=e)