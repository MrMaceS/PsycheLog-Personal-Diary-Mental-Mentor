from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.auth_service import AuthService
from app.models.user import User
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class UserService:
    """Сервис для управления профилем пользователя."""

    # Ключи трёх обязательных согласий
    CONSENT_FIELDS = (
        "consent_data_processing",
        "consent_local_cache",
        "consent_cloud_ai",
    )

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
    def snapshot_consents(user: User) -> dict[str, bool]:
        """
        Снимок текущих согласий пользователя.
        Вызывается ДО обновления, чтобы потом определить, что именно отозвали.
        """
        return {field: bool(getattr(user, field, False)) for field in UserService.CONSENT_FIELDS}

    @staticmethod
    def get_newly_revoked(previous: dict[str, bool], user: User) -> list[str]:
        """
        Возвращает список согласий, которые были ОТЗВАНЫ в этом запросе
        (было True -> стало False).

        Это чистая функция: не трогает БД и не делает commit.
        """
        revoked: list[str] = []

        for field in UserService.CONSENT_FIELDS:
            was = previous.get(field, False)
            now = bool(getattr(user, field, False))
            if was and not now:
                revoked.append(field)

        return revoked

    @staticmethod
    def can_use_cloud_ai(user: User) -> bool:
        """
        Разрешено ли отправлять данные пользователя в облачный AI.
        Будет использоваться ai_router на Спринте 3.
        """
        return bool(user.consent_cloud_ai) and bool(user.consent_data_processing)

    @staticmethod
    def can_use_local_cache(user: User) -> bool:
        """
        Разрешено ли хранить данные пользователя в локальном кэше.
        """
        return bool(user.consent_local_cache) and bool(user.consent_data_processing)

    @staticmethod
    async def delete_account(
        db: AsyncSession,
        user: User,
    ) -> bool:
        """
        Мягкое удаление аккаунта с отзывом всех сессий.

        В одной транзакции:
        1. Отзываем ВСЕ refresh-сессии (иначе пользователь останется
           залогиненным на других устройствах).
        2. Помечаем пользователя удалённым.
        """

        revoked_count = await AuthService.revoke_all_user_sessions(
            db=db,
            user_id=user.id,
        )

        user.is_active = False
        user.is_deleted = True
        user.deleted_at = datetime.now(timezone.utc)

        await db.commit()

        logger.info(
            "account_deleted",
            user_id=user.id,
            revoked_sessions=revoked_count,
        )

        return True