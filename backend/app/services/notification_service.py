from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone

from app.models.notification import Notification, NotificationType
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class NotificationService:
    @staticmethod
    async def create_notification(
            db: AsyncSession,
            user_id: int,
            notification_type: NotificationType,
            title: Optional[str],
            message: str,
            data: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Создаёт новое уведомление для пользователя."""
        import json

        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            data=json.dumps(data) if data else None,
        )
        db.add(notification)
        await db.flush()

        logger.info(
            "notification_created",
            notification_id=notification.id,
            user_id=user_id,
            type=notification_type.value,
        )

        return notification

    @staticmethod
    async def get_user_notifications(
            db: AsyncSession,
            user_id: int,
            limit: int = 20,
            offset: int = 0,
    ) -> List[Notification]:
        """Получает список уведомлений пользователя."""
        result = await db.execute(
            select(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_deleted == False,
            )
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_unread_count(
            db: AsyncSession,
            user_id: int,
    ) -> int:
        """Получает количество непрочитанных уведомлений."""
        from sqlalchemy import func

        result = await db.execute(
            select(func.count(Notification.id))
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.is_deleted == False,
            )
        )
        return result.scalar() or 0

    @staticmethod
    async def mark_as_read(
            db: AsyncSession,
            notification_id: int,
            user_id: int,
    ) -> Optional[Notification]:
        """Помечает уведомление как прочитанное."""
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()

        if not notification:
            return None

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            await db.flush()

            logger.info(
                "notification_marked_read",
                notification_id=notification.id,
                user_id=user_id,
            )

        return notification

    @staticmethod
    async def mark_all_as_read(
            db: AsyncSession,
            user_id: int,
    ) -> int:
        """Помечает все уведомления пользователя как прочитанные."""
        result = await db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.is_deleted == False,
            )
            .values(
                is_read=True,
                read_at=datetime.now(timezone.utc),
            )
        )

        logger.info(
            "all_notifications_marked_read",
            user_id=user_id,
            count=result.rowcount,
        )

        return result.rowcount