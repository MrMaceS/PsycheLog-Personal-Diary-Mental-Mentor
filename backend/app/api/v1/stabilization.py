from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.models.user import User
from app.schemas.stabilization import (
    StabilizationSessionResponse,
    StabilizationCompleteRequest,
)
from app.services.stabilization_service import StabilizationService
from app.api.v1.diary import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix="/stabilization", tags=["Stabilization"])


@router.post("/start", response_model=StabilizationSessionResponse)
async def start_stabilization(
        current_user: User = Depends(get_current_user),
):
    """
    Начало сеанса стабилизации.
    Возвращает инструкцию для выполнения прямо сейчас.
    """
    return StabilizationService.start_session(user=current_user)


@router.post("/complete")
async def complete_stabilization(
        request: StabilizationCompleteRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """
    Завершение сеанса стабилизации.
    Опционально можно указать настроение после и краткую заметку.
    """
    result = StabilizationService.complete_session(
        user=current_user,
        session_id=request.session_id,
        mood_after=request.mood_after,
        brief_note=request.brief_note,
    )

    return result