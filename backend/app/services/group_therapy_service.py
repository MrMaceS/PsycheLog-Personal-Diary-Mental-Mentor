from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from fastapi import HTTPException, status

from app.models.mediation import GroupSession, GroupEnrollment, GroupSessionStatus
from app.models.user import User
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class GroupTherapyService:
    @staticmethod
    async def create_session(
        db: AsyncSession,
        host: User,
        title: str,
        description: Optional[str],
        scheduled_at: datetime,
        duration_minutes: int = 60,
        max_participants: int = 10,
    ) -> GroupSession:
        """Создаёт новую групповую сессию."""
        if scheduled_at <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Время сессии должно быть в будущем",
            )

        session = GroupSession(
            title=title,
            description=description,
            host_id=host.id,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            max_participants=max_participants,
            status=GroupSessionStatus.SCHEDULED,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        logger.info(
            "group_session_created",
            session_id=session.id,
            host_id=host.id,
            scheduled_at=scheduled_at.isoformat(),
        )

        return session

    @staticmethod
    async def enroll_in_session(
        db: AsyncSession,
        session_id: int,
        user: User,
    ) -> GroupEnrollment:
        """Записывает пользователя на групповую сессию."""
        result = await db.execute(
            select(GroupSession).where(GroupSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия не найдена",
            )

        if session.status != GroupSessionStatus.SCHEDULED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Запись невозможна: сессия имеет статус {session.status.value}",
            )

        existing_result = await db.execute(
            select(GroupEnrollment).where(
                GroupEnrollment.session_id == session_id,
                GroupEnrollment.user_id == user.id,
            )
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Вы уже записаны на эту сессию",
            )

        count_result = await db.execute(
            select(func.count(GroupEnrollment.id)).where(
                GroupEnrollment.session_id == session_id
            )
        )
        current_count = count_result.scalar() or 0

        if current_count >= session.max_participants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Достигнут лимит участников",
            )

        enrollment = GroupEnrollment(
            session_id=session_id,
            user_id=user.id,
            enrolled_at=datetime.now(timezone.utc),
        )
        db.add(enrollment)
        await db.commit()
        await db.refresh(enrollment)

        logger.info(
            "user_enrolled_in_session",
            session_id=session_id,
            user_id=user.id,
            current_count=current_count + 1,
            max_participants=session.max_participants,
        )

        return enrollment

    @staticmethod
    async def cancel_enrollment(
        db: AsyncSession,
        session_id: int,
        user: User,
    ) -> bool:
        """Отменяет запись пользователя на сессию."""
        result = await db.execute(
            select(GroupEnrollment).where(
                GroupEnrollment.session_id == session_id,
                GroupEnrollment.user_id == user.id,
            )
        )
        enrollment = result.scalar_one_or_none()

        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Вы не записаны на эту сессию",
            )

        await db.delete(enrollment)
        await db.commit()

        logger.info(
            "enrollment_cancelled",
            session_id=session_id,
            user_id=user.id,
        )

        return True

    @staticmethod
    async def get_available_sessions(
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0,
    ) -> List[GroupSession]:
        """Получает список доступных для записи сессий."""
        result = await db.execute(
            select(GroupSession)
            .where(
                GroupSession.status == GroupSessionStatus.SCHEDULED,
                GroupSession.scheduled_at > datetime.now(timezone.utc),
                GroupSession.is_deleted == False,
            )
            .order_by(GroupSession.scheduled_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_user_enrollments(
        db: AsyncSession,
        user: User,
    ) -> List[GroupSession]:
        """Получает список сессий, на которые записан пользователь."""
        result = await db.execute(
            select(GroupSession)
            .join(GroupEnrollment)
            .where(
                GroupEnrollment.user_id == user.id,
                GroupSession.is_deleted == False,
            )
            .order_by(GroupSession.scheduled_at.asc())
        )
        return list(result.scalars().all())