from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status

from app.models.mediation import (
    MediationSession, MediationConsent, MediationSubmission,
    MediationStatus
)
from app.models.user import User
from app.services.notification_service import NotificationService
from app.models.notification import NotificationType
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class MediationService:
    @staticmethod
    async def request_mediation(
            db: AsyncSession,
            initiator: User,
            recipient_id: int,
            topic: Optional[str],
    ) -> MediationSession:
        """Создаёт запрос на медиацию и отправляет уведомление получателю."""
        if initiator.id == recipient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя запросить медиацию с самим собой",
            )

        result = await db.execute(
            select(User).where(User.id == recipient_id)
        )
        recipient = result.scalar_one_or_none()
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Получатель не найден",
            )

        session = MediationSession(
            initiator_id=initiator.id,
            recipient_id=recipient_id,
            topic=topic,
            status=MediationStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db.add(session)
        await db.flush()

        initiator_consent = MediationConsent(
            session_id=session.id,
            user_id=initiator.id,
            is_accepted=True,
            responded_at=datetime.now(timezone.utc),
        )
        db.add(initiator_consent)

        recipient_consent = MediationConsent(
            session_id=session.id,
            user_id=recipient_id,
            is_accepted=None,
        )
        db.add(recipient_consent)

        await db.commit()
        await db.refresh(session)

        await NotificationService.create_notification(
            db=db,
            user_id=recipient_id,
            notification_type=NotificationType.MEDIATION_REQUEST,
            title=f"Запрос на медиацию от {initiator.display_name}",
            message=topic or "Пользователь хочет начать медиацию с вами",
            data={"session_id": session.id, "initiator_id": initiator.id},
        )
        await db.commit()

        logger.info(
            "mediation_requested",
            session_id=session.id,
            initiator_id=initiator.id,
            recipient_id=recipient_id,
        )

        return session

    @staticmethod
    async def respond_to_mediation(
            db: AsyncSession,
            session_id: int,
            user: User,
            is_accepted: bool,
            response_message: Optional[str],
    ) -> MediationSession:
        """Получатель отвечает на запрос медиации."""
        result = await db.execute(
            select(MediationSession).where(MediationSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия медиации не найдена",
            )

        if session.recipient_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только получатель может ответить на запрос",
            )

        if session.status != MediationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Сессия уже имеет статус: {session.status.value}",
            )

        if session.expires_at and datetime.now(timezone.utc) > session.expires_at:
            session.status = MediationStatus.EXPIRED
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Срок действия запроса истёк",
            )

        consent_result = await db.execute(
            select(MediationConsent).where(
                MediationConsent.session_id == session_id,
                MediationConsent.user_id == user.id,
            )
        )
        consent = consent_result.scalar_one_or_none()

        if consent:
            consent.is_accepted = is_accepted
            consent.response_message = response_message
            consent.responded_at = datetime.now(timezone.utc)

        if is_accepted:
            session.status = MediationStatus.ACTIVE
            logger.info("mediation_accepted", session_id=session.id, user_id=user.id)

            await NotificationService.create_notification(
                db=db,
                user_id=session.initiator_id,
                notification_type=NotificationType.MEDIATION_UPDATE,
                title="Медиация принята",
                message=f"{user.display_name} согласился на медиацию",
                data={"session_id": session.id},
            )
        else:
            session.status = MediationStatus.DECLINED
            logger.info("mediation_declined", session_id=session.id, user_id=user.id)

            await NotificationService.create_notification(
                db=db,
                user_id=session.initiator_id,
                notification_type=NotificationType.MEDIATION_UPDATE,
                title="Медиация отклонена",
                message=f"{user.display_name} отклонил запрос на медиацию",
                data={"session_id": session.id},
            )

        await db.commit()
        await db.refresh(session)

        return session

    @staticmethod
    async def submit_position(
        db: AsyncSession,
        session_id: int,
        user: User,
        content: str,
        is_final: bool = False,
    ) -> MediationSubmission:
        """Пользователь отправляет свою позицию/аргумент в медиации."""
        result = await db.execute(
            select(MediationSession).where(MediationSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия медиации не найдена",
            )

        if user.id not in [session.initiator_id, session.recipient_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы не являетесь участником этой медиации",
            )

        if session.status != MediationStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Медиация не активна",
            )

        if user.id == session.initiator_id and session.initiator_submitted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Вы уже отправили свою позицию",
            )
        if user.id == session.recipient_id and session.recipient_submitted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Вы уже отправили свою позицию",
            )

        submission = MediationSubmission(
            session_id=session_id,
            user_id=user.id,
            content=content,
            is_final=is_final,
        )
        db.add(submission)

        if user.id == session.initiator_id:
            session.initiator_submitted = True
        else:
            session.recipient_submitted = True

        if session.initiator_submitted and session.recipient_submitted:
            session.status = MediationStatus.SUBMISSIONS_COMPLETE

        await db.commit()
        await db.refresh(submission)

        logger.info(
            "mediation_submission_created",
            submission_id=submission.id,
            session_id=session_id,
            user_id=user.id,
            initiator_submitted=session.initiator_submitted,
            recipient_submitted=session.recipient_submitted,
        )

        return submission

    @staticmethod
    async def get_my_submission(
        db: AsyncSession,
        session_id: int,
        user: User,
    ) -> Optional[MediationSubmission]:
        """Получает ТОЛЬКО МОЮ позицию (для слепой зоны)."""
        result = await db.execute(
            select(MediationSession).where(MediationSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия медиации не найдена",
            )

        if user.id not in [session.initiator_id, session.recipient_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы не являетесь участником этой медиации",
            )

        submission_result = await db.execute(
            select(MediationSubmission).where(
                MediationSubmission.session_id == session_id,
                MediationSubmission.user_id == user.id,
            )
        )
        return submission_result.scalar_one_or_none()

    @staticmethod
    async def get_all_submissions(
        db: AsyncSession,
        session_id: int,
        user: User,
    ) -> List[MediationSubmission]:
        """Получает ВСЕ позиции (доступно только после отправки своей)."""
        result = await db.execute(
            select(MediationSession).where(MediationSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия медиации не найдена",
            )

        if user.id not in [session.initiator_id, session.recipient_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы не являетесь участником этой медиации",
            )

        user_submitted = (
            (user.id == session.initiator_id and session.initiator_submitted) or
            (user.id == session.recipient_id and session.recipient_submitted)
        )

        if not user_submitted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы должны сначала отправить свою позицию",
            )

        submissions_result = await db.execute(
            select(MediationSubmission)
            .where(MediationSubmission.session_id == session_id)
            .order_by(MediationSubmission.created_at.asc())
        )
        return list(submissions_result.scalars().all())

    @staticmethod
    async def get_user_mediations(
            db: AsyncSession,
            user: User,
    ) -> List[MediationSession]:
        """Получает все медиации пользователя (как инициатора или получателя)."""
        result = await db.execute(
            select(MediationSession).where(
                (MediationSession.initiator_id == user.id) |
                (MediationSession.recipient_id == user.id),
                MediationSession.is_deleted == False,
            ).order_by(MediationSession.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def confirm_resolution(
            db: AsyncSession,
            session_id: int,
            user: User,
            is_confirmed: bool,
    ) -> MediationSession:
        """
        Подтверждение или отклонение AI-резюме.
        Требует согласия обоих участников для статуса CONFIRMED.
        Если один отклоняет - статус DISPUTED.
        """
        result = await db.execute(
            select(MediationSession).where(MediationSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия медиации не найдена",
            )

        if user.id not in [session.initiator_id, session.recipient_id]:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы не являетесь участником этой медиации",
            )

        if session.status != MediationStatus.RESOLUTION_PROPOSED:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Подтверждение доступно только после получения AI-резюме",
            )

        if not is_confirmed:
            session.status = MediationStatus.DISPUTED
            await db.commit()
            await db.refresh(session)

            logger.info(
                "mediation_resolution_disputed",
                session_id=session_id,
                user_id=user.id,
            )
            return session

        # Если пользователь подтверждает
        # Проверяем, подтвердил ли уже другой участник
        # Используем простую логику: если оба подтвердили - CONFIRMED
        # Для этого добавим временные поля в модель (см. ниже)

        # Временно используем существующие поля для отслеживания
        # В реальном проекте лучше добавить initiator_confirmed и recipient_confirmed

        # Для простоты: если это первый подтвердивший - ждём второго
        # Если это второй - меняем статус на CONFIRMED

        # Проверяем, есть ли уже запись о подтверждении в ai_summary
        # (используем как временный флаг)
        if session.ai_summary and "confirmed_by_initiator" in session.ai_summary:
            if user.id == session.recipient_id:
                session.status = MediationStatus.CONFIRMED
                session.completed_at = datetime.now(timezone.utc)
        elif session.ai_summary and "confirmed_by_recipient" in session.ai_summary:
            if user.id == session.initiator_id:
                session.status = MediationStatus.CONFIRMED
                session.completed_at = datetime.now(timezone.utc)
        else:
            if not session.ai_summary:
                session.ai_summary = ""

            if user.id == session.initiator_id:
                session.ai_summary += "|confirmed_by_initiator"
            else:
                session.ai_summary += "|confirmed_by_recipient"

        await db.commit()
        await db.refresh(session)

        logger.info(
            "mediation_resolution_confirmed",
            session_id=session_id,
            user_id=user.id,
            new_status=session.status.value,
        )

        return session