"""Dependency injection for API endpoints."""

import logging
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db.connection import get_db as get_db_session
from app.core.security.jwt import decode_token
from app.models.user import User
from app.repositories.user import UserRepository

# Import permissions module to set get_current_active_user
import app.core.security.permissions as permissions_module

# Configure logging
logger = logging.getLogger(__name__)

# OAuth2 token URL for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.

    Returns:
        Generator[Session, None, None]: Database session
    """
    return get_db_session()


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """
    Get user repository.

    Args:
        db: Database session

    Returns:
        UserRepository: User repository
    """
    return UserRepository(db)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """
    Get the current authenticated user.

    Args:
        token: JWT token
        user_repo: User repository

    Returns:
        User: Current user

    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Decode the token
        payload = decode_token(token)
        user_id: Optional[str] = payload.get("sub")

        if user_id is None:
            logger.warning("Token payload missing 'sub' field")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except HTTPException:
        # Re-raise HTTPExceptions from decode_token
        raise
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get the user from the database
    user = user_repo.get_by_id(int(user_id))
    if user is None:
        logger.warning(f"User with ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active user.

    Args:
        current_user: Current user

    Returns:
        User: Current active user

    Raises:
        HTTPException: If the user is inactive
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user {current_user.id} attempted to access the API")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return current_user

# Set get_current_active_user in permissions module to avoid circular imports
permissions_module.get_current_active_user = get_current_active_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get the current superuser.

    Args:
        current_user: Current active user

    Returns:
        User: Current superuser

    Raises:
        HTTPException: If the user is not a superuser
    """
    if not current_user.is_superuser:
        logger.warning(
            f"Non-superuser {current_user.id} attempted to access superuser-only endpoint"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    return current_user


async def get_current_user_from_token(
    token: str,
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """
    Get the current user from a token without using OAuth2PasswordBearer.

    This is useful for WebSocket authentication where the token is passed as a query parameter.

    Args:
        token: JWT token
        user_repo: User repository

    Returns:
        User: Current user

    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Decode the token
        payload = decode_token(token)
        user_id: Optional[str] = payload.get("sub")

        if user_id is None:
            logger.warning("Token payload missing 'sub' field")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except HTTPException:
        # Re-raise HTTPExceptions from decode_token
        raise
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get the user from the database
    user = user_repo.get_by_id(int(user_id))
    if user is None:
        logger.warning(f"User with ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Inactive user {user.id} attempted to access the API")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user
