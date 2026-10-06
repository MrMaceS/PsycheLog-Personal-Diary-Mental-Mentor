from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.user_service import UserService
from app.schemas.user import UserResponse, UpdateUserRequest, UpdateConsentsRequest, DeleteAccountRequest
from app.core.security import verify_token, verify_pin
from fastapi import APIRouter, Depends, HTTPException, status, Security
from app.core.logging_config import get_logger
from app.models.user import User
from fastapi.security import HTTPAuthorizationCredentials
from app.core.security_scheme import security

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Security(security),
        db: AsyncSession = Depends(get_db),
) -> User:
    """Получение текущего пользователя из токена."""
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


@router.get("/me", response_model=UserResponse)
async def get_current_user_endpoint(
        current_user: User = Depends(get_current_user),
):
    """Получение текущего профиля."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
        request: UpdateUserRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Обновление профиля."""
    user = await UserService.update_user(
        db=db,
        user=current_user,
        display_name=request.display_name,
        avatar_url=request.avatar_url,
    )
    return user


@router.patch("/me/consents", response_model=UserResponse)
async def update_consents(
        request: UpdateConsentsRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Обновление согласий."""
    user = await UserService.update_consents(
        db=db,
        user=current_user,
        consent_data_processing=request.consent_data_processing,
        consent_local_cache=request.consent_local_cache,
        consent_cloud_ai=request.consent_cloud_ai,
    )
    return user


@router.delete("/me")
async def delete_account(
    request: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Удаление аккаунта."""
    if not verify_pin(
        request.pin,
        current_user.hashed_pin,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный PIN",
        )

    await UserService.delete_account(
        db=db,
        user=current_user,
    )

    return {"message": "Аккаунт удалён"}