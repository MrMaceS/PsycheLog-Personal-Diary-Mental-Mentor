from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.diary_service import DiaryService
from app.schemas.diary import CreateDiaryEntry, UpdateDiaryEntry, DiaryEntryResponse
from app.core.security import verify_token
from fastapi import APIRouter, Depends, HTTPException, status, Security, Query
from app.core.logging_config import get_logger
from app.models.user import User
from fastapi.security import HTTPAuthorizationCredentials
from app.core.security_scheme import security

logger = get_logger(__name__)

router = APIRouter(prefix="/diary", tags=["Diary"])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Получение текущего пользователя из токена."""
    from app.services.user_service import UserService

    token = credentials.credentials
    payload = verify_token(token, token_type="access")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload["sub"])
    user = await UserService.get_user_by_id(db, user_id)

    if not user or not user.is_active or user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@router.post("/", response_model=DiaryEntryResponse)
async def create_diary_entry(
    request: CreateDiaryEntry,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создание новой записи дневника."""
    entry = await DiaryService.create_entry(
        db=db,
        user_id=current_user.id,
        title=request.title,
        content=request.content,
        mood=request.mood,
        tags=request.tags,
    )

    return entry


@router.get("/", response_model=list[DiaryEntryResponse])
async def list_diary_entries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Список записей дневника пользователя."""
    entries = await DiaryService.get_entries_by_user(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )

    return entries


@router.get("/{entry_id}", response_model=DiaryEntryResponse)
async def get_diary_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получение одной записи дневника."""
    entry = await DiaryService.get_entry_by_id(
        db=db,
        entry_id=entry_id,
        user_id=current_user.id,
    )

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запись не найдена",
        )

    return entry


@router.patch("/{entry_id}", response_model=DiaryEntryResponse)
async def update_diary_entry(
    entry_id: int,
    request: UpdateDiaryEntry,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновление записи дневника."""
    entry = await DiaryService.get_entry_by_id(
        db=db,
        entry_id=entry_id,
        user_id=current_user.id,
    )

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запись не найдена",
        )

    updated = await DiaryService.update_entry(
        db=db,
        entry=entry,
        title=request.title,
        content=request.content,
        mood=request.mood,
        tags=request.tags,
    )

    return updated


@router.delete("/{entry_id}")
async def delete_diary_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Мягкое удаление записи дневника."""
    entry = await DiaryService.get_entry_by_id(
        db=db,
        entry_id=entry_id,
        user_id=current_user.id,
    )

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запись не найдена",
        )

    await DiaryService.delete_entry(
        db=db,
        entry=entry,
    )

    return {"message": "Запись удалена"}