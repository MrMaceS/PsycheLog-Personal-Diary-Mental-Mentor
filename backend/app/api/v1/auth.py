from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    OTPRequest,
    VerifyOTPRequest,
    RecoverAccountRequest,
)
from app.core.logging_config import get_logger
from app.core.config import settings

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя."""
    try:
        user, tokens = await AuthService.register_user(
            db=db,
            email=request.email,
            username=request.username,
            display_name=request.display_name,
            pin=request.pin,
            avatar_url=request.avatar_url,
        )
        return TokenResponse(**tokens)
    except ValueError as e:
        logger.warning("registration_failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Вход пользователя."""
    try:
        tokens = await AuthService.login_user(
            db=db,
            email=request.email,
            pin=request.pin,
        )
        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или PIN",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenResponse(**tokens)
    except ValueError as e:
        if "заблокирован" in str(e):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или PIN",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Обновление токенов."""
    tokens = await AuthService.refresh_tokens(db=db, refresh_token=request.refresh_token)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(**tokens)


@router.post("/logout")
async def logout(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Выход пользователя."""
    success = await AuthService.logout_user(db=db, refresh_token=request.refresh_token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный refresh token",
        )
    return {"message": "Выход выполнен успешно"}


@router.post("/request-otp")
async def request_otp(request: OTPRequest, db: AsyncSession = Depends(get_db)):
    """Запрос OTP для восстановления аккаунта."""
    success, otp = await AuthService.request_otp(
        db=db,
        email=request.email,
        purpose="account_recovery"
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось отправить OTP",
        )

    response = {
        "message": "OTP отправлен на email",
    }

    if settings.ENVIRONMENT == "test":
        response["otp"] = otp

    return response


@router.post("/verify-otp")
async def verify_otp(request: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    """Проверка OTP."""
    success = await AuthService.verify_otp(db=db, email=request.email, otp=request.otp)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или истёкший OTP",
        )
    return {"message": "OTP подтверждён"}


@router.post("/recover-account")
async def recover_account(request: RecoverAccountRequest, db: AsyncSession = Depends(get_db)):
    """Восстановление аккаунта через OTP."""
    success = await AuthService.recover_account(
        db=db,
        email=request.email,
        otp=request.otp,
        new_pin=request.new_pin,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось восстановить аккаунт",
        )
    return {"message": "Аккаунт восстановлен"}