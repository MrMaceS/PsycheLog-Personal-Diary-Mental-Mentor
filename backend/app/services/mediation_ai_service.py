from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.models.mediation import MediationSession, MediationSubmission, MediationStatus
from app.models.user import User
from app.ai.ai_service import ai_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class MediationAIService:
    @staticmethod
    async def analyze_mediation(
            db: AsyncSession,
            session_id: int,
            current_user: User,
    ) -> MediationSession:
        """
        Запускает AI-анализ медиации.
        Доступно только когда оба участника отправили свои позиции.
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

        if current_user.id not in [session.initiator_id, session.recipient_id]:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы не являетесь участником этой медиации",
            )

        if session.status != MediationStatus.SUBMISSIONS_COMPLETE:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="AI-анализ доступен только после отправки обеих позиций",
            )

        session.status = MediationStatus.AI_ANALYSIS
        await db.commit()

        submissions_result = await db.execute(
            select(MediationSubmission).where(
                MediationSubmission.session_id == session_id
            )
        )
        submissions = submissions_result.scalars().all()

        initiator_submission = next(
            (s for s in submissions if s.user_id == session.initiator_id), None
        )
        recipient_submission = next(
            (s for s in submissions if s.user_id == session.recipient_id), None
        )

        if not initiator_submission or not recipient_submission:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не найдены позиции обоих участников",
            )

        initiator_result = await db.execute(
            select(User).where(User.id == session.initiator_id)
        )
        initiator = initiator_result.scalar_one()

        recipient_result = await db.execute(
            select(User).where(User.id == session.recipient_id)
        )
        recipient = recipient_result.scalar_one()

        try:
            prompt = f"""Ты - профессиональный медиатор и психолог. Проанализируй конфликт между двумя людьми и дай рекомендации.

Тема конфликта: {session.topic or 'Не указана'}

Позиция Участника 1 ({initiator.display_name}):
{initiator_submission.content}

Позиция Участника 2 ({recipient.display_name}):
{recipient_submission.content}

Задание:
1. Определи корневую причину конфликта
2. Найди точки соприкосновения
3. Предложи конкретные шаги для разрешения ситуации

Ответ должен быть структурированным, эмпатичным и практичным. Длина: 300-500 слов."""

            ai_response = await ai_service.generate_response(
                prompt=prompt,
                system_prompt="Ты - профессиональный медиатор и психолог с 20-летним опытом.",
            )

            session.resolution = ai_response
            session.status = MediationStatus.RESOLUTION_PROPOSED
            session.completed_at = datetime.now(timezone.utc)

            initiator_private = await MediationAIService._generate_private_recommendation(
                session.topic,
                initiator_submission.content,
                recipient_submission.content,
                is_initiator=True,
            )
            initiator_submission.ai_analysis = initiator_private

            recipient_private = await MediationAIService._generate_private_recommendation(
                session.topic,
                initiator_submission.content,
                recipient_submission.content,
                is_initiator=False,
            )
            recipient_submission.ai_analysis = recipient_private

            await db.commit()
            await db.refresh(session)

            logger.info(
                "mediation_ai_analysis_completed",
                session_id=session_id,
                resolution_length=len(ai_response),
            )

            return session

        except Exception as e:
            session.status = MediationStatus.SUBMISSIONS_COMPLETE
            await db.commit()
            logger.error("mediation_ai_analysis_failed", session_id=session_id, error=str(e))
            raise

    @staticmethod
    async def _generate_private_recommendation(
            topic: Optional[str],
            my_position: str,
            other_position: str,
            is_initiator: bool,
    ) -> str:
        """
        Генерирует приватную рекомендацию для одного участника.
        Не раскрывает позицию другого участника.
        """
        role = "Участник 1" if is_initiator else "Участник 2"

        prompt = f"""Ты - профессиональный медиатор. Дай персональную рекомендацию для {role}.

Тема конфликта: {topic or 'Не указана'}

Позиция {role}:
{my_position}

Контекст (не показывай это пользователю): Вторая сторона тоже имеет свою позицию, но мы не будем её раскрывать.

Задание:
1. Признай чувства и concerns {role}
2. Предложи 2-3 конкретных шага, которые {role} может предпринять
3. Дай совет по коммуникации с другой стороной

Ответ должен быть эмпатичным, практичным и конфиденциальным. Длина: 150-250 слов."""

        try:
            response = await ai_service.generate_response(
                prompt=prompt,
                system_prompt="Ты - профессиональный медиатор. Давай персональные, конфиденциальные рекомендации.",
            )
            return response
        except Exception as e:
            logger.error("private_recommendation_generation_failed", error=str(e))
            return "AI-рекомендации временно недоступны. Пожалуйста, попробуйте позже."