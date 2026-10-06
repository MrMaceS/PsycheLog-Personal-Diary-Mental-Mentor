from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    pin: str = Field(..., min_length=4, max_length=4)
    avatar_url: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username может содержать только буквы, цифры и подчёркивание")
        return v

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("PIN должен состоять из 4 цифр")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    pin: str = Field(..., min_length=4, max_length=4)

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("PIN должен состоять из 4 цифр")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class OTPRequest(BaseModel):
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("OTP должен состоять из 6 цифр")
        return v


class RecoverAccountRequest(BaseModel):
    email: EmailStr
    otp: str
    new_pin: str = Field(..., min_length=4, max_length=4)

    @field_validator("new_pin")
    @classmethod
    def validate_new_pin(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("PIN должен состоять из 4 цифр")
        return v