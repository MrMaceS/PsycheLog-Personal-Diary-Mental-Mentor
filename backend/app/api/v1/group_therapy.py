from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.models.user import User
from app.models.mediation import GroupSession, GroupEnrollment
from app.schemas.group_therapy import (
    GroupSessionCreate,
    GroupSessionResponse,
    GroupEnrollmentResponse,
)
from app.services.group_therapy_service import GroupTherapyService
from app.api.v1.diary import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix="/group-therapy", tags=["Group Therapy"])


@router.post(
    "/sessions",
    response_model=GroupSessionResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_session(
        request: GroupSessionCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Создать новую групповую сессию."""
    session = await GroupTherapyService.create_session(
        db=db,
        host=current_user,
        title=request.title,
        description=request.description,
        scheduled_at=request.scheduled_at,
        duration_minutes=request.duration_minutes,
        max_participants=request.max_participants,
    )

    return GroupSessionResponse(
        id=session.id,
        title=session.title,
        description=session.description,
        host_id=session.host_id,
        scheduled_at=session.scheduled_at,
        duration_minutes=session.duration_minutes,
        max_participants=session.max_participants,
        status=session.status,
        created_at=session.created_at,
        enrolled_count=0,
    )


@router.get("/sessions", response_model=List[GroupSessionResponse])
async def list_available_sessions(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
):
    """Получить список доступных для записи групповых сессий."""
    sessions = await GroupTherapyService.get_available_sessions(
        db=db,
        limit=limit,
        offset=offset,
    )

    response = []
    for session in sessions:
        count_result = await db.execute(
            select(func.count(GroupEnrollment.id)).where(
                GroupEnrollment.session_id == session.id
            )
        )
        enrolled_count = count_result.scalar() or 0

        response.append(
            GroupSessionResponse(
                id=session.id,
                title=session.title,
                description=session.description,
                host_id=session.host_id,
                scheduled_at=session.scheduled_at,
                duration_minutes=session.duration_minutes,
                max_participants=session.max_participants,
                status=session.status,
                created_at=session.created_at,
                enrolled_count=enrolled_count,
            )
        )

    return response


@router.get("/sessions/my-enrollments", response_model=List[GroupSessionResponse])
async def list_my_enrollments(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Получить список сессий, на которые я записан."""
    sessions = await GroupTherapyService.get_user_enrollments(
        db=db,
        user=current_user,
    )

    response = []
    for session in sessions:
        count_result = await db.execute(
            select(func.count(GroupEnrollment.id)).where(
                GroupEnrollment.session_id == session.id
            )
        )
        enrolled_count = count_result.scalar() or 0

        response.append(
            GroupSessionResponse(
                id=session.id,
                title=session.title,
                description=session.description,
                host_id=session.host_id,
                scheduled_at=session.scheduled_at,
                duration_minutes=session.duration_minutes,
                max_participants=session.max_participants,
                status=session.status,
                created_at=session.created_at,
                enrolled_count=enrolled_count,
            )
        )

    return response


@router.post("/sessions/{session_id}/enroll", response_model=GroupEnrollmentResponse,
             status_code=status.HTTP_201_CREATED)
async def enroll_in_session(
        session_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Записаться на групповую сессию."""
    enrollment = await GroupTherapyService.enroll_in_session(
        db=db,
        session_id=session_id,
        user=current_user,
    )
    return enrollment


@router.delete("/sessions/{session_id}/enroll")
async def cancel_enrollment(
        session_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Отменить запись на групповую сессию."""
    await GroupTherapyService.cancel_enrollment(
        db=db,
        session_id=session_id,
        user=current_user,
    )
    return {"message": "Запись отменена"}