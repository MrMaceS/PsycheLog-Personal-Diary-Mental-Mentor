from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.logging_config import get_logger
from datetime import datetime, timezone

logger = get_logger(__name__)


class UserService:
    """Сервис для управления профилем пользователя."""

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Получение пользователя по ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user(
            db: AsyncSession,
            user: User,
            display_name: Optional[str] = None,
            avatar_url: Optional[str] = None,
    ) -> User:
        """Обновление профиля пользователя."""
        if display_name is not None:
            user.display_name = display_name
        if avatar_url is not None:
            user.avatar_url = avatar_url

        await db.flush()
        logger.info("user_updated", user_id=user.id)

        return user

    @staticmethod
    async def update_consents(
            db: AsyncSession,
            user: User,
            consent_data_processing: Optional[bool] = None,
            consent_local_cache: Optional[bool] = None,
            consent_cloud_ai: Optional[bool] = None,
    ) -> User:
        """Обновление согласий пользователя."""
        if consent_data_processing is not None:
            user.consent_data_processing = consent_data_processing
        if consent_local_cache is not None:
            user.consent_local_cache = consent_local_cache
        if consent_cloud_ai is not None:
            user.consent_cloud_ai = consent_cloud_ai

        await db.flush()
        logger.info("user_consents_updated", user_id=user.id)

        return user

    @staticmethod
    async def delete_account(db: AsyncSession, user: User) -> bool:
        """Удаление аккаунта (мягкое)."""
        user.is_active = False
        user.is_deleted = True
        user.deleted_at = datetime.now(timezone.utc)

        await db.flush()
        logger.info("account_deleted", user_id=user.id)

        return True