"""
Schemas package for the MAGPIE platform.
"""

from app.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    Token,
    TokenPayload,
    UserBase,
    UserCreate,
    UserInDB,
    UserResponse,
    UserUpdate,
)

__all__ = [
    "LoginRequest",
    "PasswordResetConfirm",
    "PasswordResetRequest",
    "RefreshTokenRequest",
    "Token",
    "TokenPayload",
    "UserBase",
    "UserCreate",
    "UserInDB",
    "UserResponse",
    "UserUpdate",
]
