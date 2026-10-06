from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4
import bcrypt
from jose import JWTError, jwt
from app.core.config import settings


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """Проверка PIN."""

    return bcrypt.checkpw(
        plain_pin.encode("utf-8"),
        hashed_pin.encode("utf-8"),
    )


def get_pin_hash(pin: str) -> str:
    """Хеширование PIN."""

    return bcrypt.hashpw(
        pin.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Создание JWT access token."""

    now = datetime.now(timezone.utc)

    expire = now + (
        expires_delta
        or timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
    )

    to_encode = data.copy()

    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "jti": str(uuid4()),
            "type": "access",
        }
    )

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Создание JWT refresh token."""

    now = datetime.now(timezone.utc)

    expire = now + (
        expires_delta
        or timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        )
    )

    to_encode = data.copy()

    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "jti": str(uuid4()),
            "type": "refresh",
        }
    )

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> Optional[dict]:
    """Декодирование JWT token."""

    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        return None


def verify_token(
    token: str,
    token_type: str = "access",
) -> Optional[dict]:
    """Проверка JWT и его типа."""

    payload = decode_token(token)

    if payload is None:
        return None

    if payload.get("type") != token_type:
        return None

    if not payload.get("sub"):
        return None

    if not payload.get("jti"):
        return None

    return payload