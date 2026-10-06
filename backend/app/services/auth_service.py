from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import hashlib
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.auth import RefreshSession, OTPChallenge
from app.core.security import (
    get_pin_hash,
    verify_pin,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.core.config import settings
from app.core.logging_config import get_logger


logger = get_logger(__name__)


class AuthService:
    """Сервис для управления аутентификацией."""

    @staticmethod
    def now_utc() -> datetime:
        """Текущее время UTC с информацией о часовом поясе."""
        return datetime.now(timezone.utc)

    @staticmethod
    async def register_user(
        db: AsyncSession,
        email: str,
        username: str,
        display_name: str,
        pin: str,
        avatar_url: Optional[str] = None,
    ) -> Tuple[User, dict]:
        """Регистрация нового пользователя."""

        existing_user_result = await db.execute(
            select(User).where(
                (User.email == email) | (User.username == username)
            )
        )

        if existing_user_result.scalar_one_or_none():
            raise ValueError("Email или username уже заняты")

        user = User(
            email=email,
            username=username,
            display_name=display_name,
            hashed_pin=get_pin_hash(pin),
            avatar_url=avatar_url,
            consent_data_processing=False,
            consent_local_cache=False,
            consent_cloud_ai=False,
        )

        try:
            db.add(user)
            await db.flush()

            tokens = await AuthService.create_tokens(db, user.id)

            await db.commit()
            await db.refresh(user)

            logger.info(
                "user_registered",
                user_id=user.id,
                email=email,
            )

            return user, tokens

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def login_user(
        db: AsyncSession,
        email: str,
        pin: str,
    ) -> Optional[dict]:
        """Вход пользователя."""

        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active or user.is_deleted:
            logger.warning(
                "login_failed_user_not_found",
                email=email,
            )
            return None

        now = AuthService.now_utc()

        if user.locked_until and user.locked_until > now:
            logger.warning(
                "login_failed_pin_locked",
                user_id=user.id,
            )
            raise ValueError("Аккаунт заблокирован. Попробуйте позже.")

        if not verify_pin(pin, user.hashed_pin):
            user.failed_login_attempts += 1

            if (
                user.failed_login_attempts
                >= settings.PIN_FREEZE_AFTER_ATTEMPTS
            ):
                user.locked_until = now + timedelta(
                    minutes=settings.PIN_FREEZE_MINUTES
                )

                logger.warning(
                    "pin_locked",
                    user_id=user.id,
                    attempts=user.failed_login_attempts,
                )

            await db.commit()

            logger.warning(
                "login_failed_invalid_pin",
                user_id=user.id,
                attempts=user.failed_login_attempts,
            )

            return None

        user.failed_login_attempts = 0
        user.locked_until = None

        tokens = await AuthService.create_tokens(db, user.id)

        await db.commit()

        logger.info(
            "user_logged_in",
            user_id=user.id,
        )

        return tokens

    @staticmethod
    async def create_tokens(
        db: AsyncSession,
        user_id: int,
    ) -> dict:
        """Создание access и refresh токенов."""

        access_token = create_access_token(
            data={"sub": str(user_id)}
        )

        refresh_token = create_refresh_token(
            data={"sub": str(user_id)}
        )

        refresh_token_hash = hashlib.sha256(
            refresh_token.encode("utf-8")
        ).hexdigest()

        session = RefreshSession(
            user_id=user_id,
            token_hash=refresh_token_hash,
            expires_at=AuthService.now_utc()
            + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            ),
        )

        db.add(session)
        await db.flush()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    async def refresh_tokens(
        db: AsyncSession,
        refresh_token: str,
    ) -> Optional[dict]:
        """Обновление access и refresh токенов."""

        payload = verify_token(
            refresh_token,
            token_type="refresh",
        )

        if not payload or "sub" not in payload:
            logger.warning(
                "refresh_failed_invalid_token"
            )
            return None

        try:
            user_id = int(payload["sub"])
        except (TypeError, ValueError):
            logger.warning(
                "refresh_failed_invalid_subject"
            )
            return None

        token_hash = hashlib.sha256(
            refresh_token.encode("utf-8")
        ).hexdigest()

        result = await db.execute(
            select(RefreshSession).where(
                (RefreshSession.token_hash == token_hash)
                & (RefreshSession.user_id == user_id)
                & (RefreshSession.is_revoked.is_(False))
                & (
                    RefreshSession.expires_at
                    > AuthService.now_utc()
                )
            )
        )

        session = result.scalar_one_or_none()

        if not session:
            logger.warning(
                "refresh_failed_session_invalid",
                user_id=user_id,
            )
            return None

        try:
            session.is_revoked = True

            tokens = await AuthService.create_tokens(
                db,
                user_id,
            )

            await db.commit()

            logger.info(
                "tokens_refreshed",
                user_id=user_id,
            )

            return tokens

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def logout_user(
        db: AsyncSession,
        refresh_token: str,
    ) -> bool:
        """Выход пользователя и отзыв refresh-токена."""

        token_hash = hashlib.sha256(
            refresh_token.encode("utf-8")
        ).hexdigest()

        result = await db.execute(
            select(RefreshSession).where(
                RefreshSession.token_hash == token_hash
            )
        )

        session = result.scalar_one_or_none()

        if not session:
            return False

        session.is_revoked = True
        await db.commit()

        logger.info(
            "user_logged_out",
            user_id=session.user_id,
        )

        return True

    @staticmethod
    async def request_otp(
        db: AsyncSession,
        email: str,
        purpose: str,
    ) -> Tuple[bool, Optional[str]]:
        """Запрос OTP для восстановления аккаунта."""

        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(
                "otp_requested_nonexistent_email",
                email=email,
            )
            return False, None

        # Шестизначный цифровой код.
        otp = f"{secrets.randbelow(1_000_000):06d}"

        otp_hash = hashlib.sha256(
            otp.encode("utf-8")
        ).hexdigest()

        await db.execute(
            OTPChallenge.__table__.delete().where(
                (OTPChallenge.email == email)
                & (OTPChallenge.purpose == purpose)
                & (OTPChallenge.is_used.is_(False))
            )
        )

        challenge = OTPChallenge(
            email=email,
            otp_hash=otp_hash,
            purpose=purpose,
            expires_at=AuthService.now_utc()
            + timedelta(
                minutes=settings.OTP_EXPIRE_MINUTES
            ),
        )

        try:
            db.add(challenge)
            await db.commit()

            logger.info(
                "otp_generated",
                email=email,
                purpose=purpose,
            )

            if settings.ENVIRONMENT == "test":
                return True, otp

            return True, None

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def verify_otp(
        db: AsyncSession,
        email: str,
        otp: str,
    ) -> bool:
        """Проверка OTP без его использования."""

        otp_hash = hashlib.sha256(
            otp.encode("utf-8")
        ).hexdigest()

        result = await db.execute(
            select(OTPChallenge).where(
                (OTPChallenge.email == email)
                & (OTPChallenge.otp_hash == otp_hash)
                & (OTPChallenge.is_used.is_(False))
                & (
                    OTPChallenge.expires_at
                    > AuthService.now_utc()
                )
            )
        )

        challenge = result.scalar_one_or_none()

        if not challenge:
            logger.warning(
                "otp_verification_failed",
                email=email,
            )
            return False

        return True

    @staticmethod
    async def recover_account(
        db: AsyncSession,
        email: str,
        otp: str,
        new_pin: str,
    ) -> bool:
        """Восстановление аккаунта через OTP."""

        otp_hash = hashlib.sha256(
            otp.encode("utf-8")
        ).hexdigest()

        otp_result = await db.execute(
            select(OTPChallenge).where(
                (OTPChallenge.email == email)
                & (OTPChallenge.otp_hash == otp_hash)
                & (OTPChallenge.is_used.is_(False))
                & (
                    OTPChallenge.expires_at
                    > AuthService.now_utc()
                )
            )
        )

        otp_challenge = otp_result.scalar_one_or_none()

        if not otp_challenge:
            logger.warning(
                "account_recovery_invalid_otp",
                email=email,
            )
            return False

        user_result = await db.execute(
            select(User).where(User.email == email)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            return False

        try:
            user.hashed_pin = get_pin_hash(new_pin)
            user.failed_login_attempts = 0
            user.locked_until = None

            otp_challenge.is_used = True

            await db.commit()

            logger.info(
                "account_recovered",
                user_id=user.id,
            )

            return True

        except Exception:
            await db.rollback()
            raise