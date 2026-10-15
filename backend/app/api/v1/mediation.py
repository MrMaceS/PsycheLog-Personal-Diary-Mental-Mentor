from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.database import get_db
from app.core.logging_config import get_logger
from app.models.user import User
from app.schemas.mediation import (
    MediationRequestCreate,
    MediationResponse,
    MediationRespondRequest,
    MediationSubmissionCreate,
    MediationSubmissionResponse,
    ConfirmResolutionRequest
)
from app.services.mediation_service import MediationService
from app.api.v1.diary import get_current_user
from sqlalchemy import select
from app.models.mediation import MediationSession, MediationSubmission
from app.services.mediation_ai_service import MediationAIService

logger = get_logger(__name__)
router = APIRouter(prefix="/mediation", tags=["Mediation"])


@router.post("/request", response_model=MediationResponse, status_code=status.HTTP_201_CREATED)
async def request_mediation(
        request: MediationRequestCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Создать запрос на медиацию с другим пользователем."""
    session = await MediationService.request_mediation(
        db=db,
        initiator=current_user,
        recipient_id=request.recipient_id,
        topic=request.topic,
    )
    return session


@router.patch("/{session_id}/respond", response_model=MediationResponse)
async def respond_to_mediation(
        session_id: int,
        request: MediationRespondRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Ответить на запрос медиации (принять или отклонить)."""
    session = await MediationService.respond_to_mediation(
        db=db,
        session_id=session_id,
        user=current_user,
        is_accepted=request.is_accepted,
        response_message=request.response_message,
    )
    return session


@router.post("/{session_id}/submit", response_model=MediationSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_position(
        session_id: int,
        request: MediationSubmissionCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Отправить свою позицию/аргумент в активной медиации."""
    submission = await MediationService.submit_position(
        db=db,
        session_id=session_id,
        user=current_user,
        content=request.content,
        is_final=request.is_final,
    )
    return submission


@router.get("/", response_model=List[MediationResponse])
async def list_my_mediations(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Получить список всех моих медиаций (как инициатора или получателя)."""
    sessions = await MediationService.get_user_mediations(
        db=db,
        user=current_user,
    )
    return sessions


@router.get("/{session_id}", response_model=MediationResponse)
async def get_mediation_session(
        session_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Получить детали конкретной сессии медиации."""
    result = await db.execute(
        select(MediationSession).where(MediationSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сессия медиации не найдена",
        )

    if current_user.id not in [session.initiator_id, session.recipient_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь участником этой медиации",
        )

    return session


@router.get(
    "/{session_id}/my-submission",
    response_model=Optional[MediationSubmissionResponse]
)
async def get_my_submission(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить ТОЛЬКО МОЮ позицию (слепая зона)."""
    submission = await MediationService.get_my_submission(
        db=db,
        session_id=session_id,
        user=current_user,
    )
    return submission


@router.get(
    "/{session_id}/all-submissions",
    response_model=List[MediationSubmissionResponse]
)
async def get_all_submissions(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить ВСЕ позиции (доступно только после отправки своей)."""
    submissions = await MediationService.get_all_submissions(
        db=db,
        session_id=session_id,
        user=current_user,
    )
    return submissions


@router.post("/{session_id}/analyze", response_model=MediationResponse)
async def analyze_mediation(
        session_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Запустить AI-анализ медиации (доступно только после отправки обеих позиций)."""

    session = await MediationAIService.analyze_mediation(
        db=db,
        session_id=session_id,
        current_user=current_user,
    )
    return session


@router.post("/{session_id}/confirm-resolution", response_model=MediationResponse)
async def confirm_resolution(
    session_id: int,
    request: ConfirmResolutionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Подтвердить или отклонить AI-резюме медиации."""
    session = await MediationService.confirm_resolution(
        db=db,
        session_id=session_id,
        user=current_user,
        is_confirmed=request.is_confirmed,
    )
    return session