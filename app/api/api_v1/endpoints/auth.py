"""
Authentication endpoints for the MAGPIE platform.
"""
import logging
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_repository
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    Token,
    UserCreate,
    UserResponse,
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository),
) -> Any:
    """
    Register a new user.
    
    Args:
        user_in: User creation data
        user_repo: User repository
        
    Returns:
        UserResponse: Created user
        
    Raises:
        HTTPException: If the user already exists
    """
    # Check if user with the same email already exists
    user = user_repo.get_by_email(user_in.email)
    if user:
        logger.warning(f"Registration attempt with existing email: {user_in.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    
    # Check if user with the same username already exists
    user = user_repo.get_by_username(user_in.username)
    if user:
        logger.warning(f"Registration attempt with existing username: {user_in.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists",
        )
    
    # Create new user
    hashed_password = get_password_hash(user_in.password)
    user_data = user_in.model_dump(exclude={"password"})
    user_data["hashed_password"] = hashed_password
    
    # Create user in database
    user = user_repo.create(user_data)
    if not user:
        logger.error(f"Failed to create user: {user_in.email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )
    
    logger.info(f"User registered: {user.email} (ID: {user.id})")
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepository = Depends(get_user_repository),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    Args:
        form_data: OAuth2 password request form
        user_repo: User repository
        
    Returns:
        Token: Access and refresh tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    # Get user by username
    user = user_repo.get_by_username(form_data.username)
    if not user:
        # Try email as username
        user = user_repo.get_by_email(form_data.username)
    
    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    # Create access token
    access_token = create_access_token(
        subject=user.id,
        data={"role": user.role.value, "username": user.username},
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(subject=user.id)
    
    logger.info(f"User logged in: {user.email} (ID: {user.id})")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    login_data: LoginRequest,
    user_repo: UserRepository = Depends(get_user_repository),
) -> Any:
    """
    Login with username and password.
    
    Args:
        login_data: Login data
        user_repo: User repository
        
    Returns:
        Token: Access and refresh tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    # Get user by username
    user = user_repo.get_by_username(login_data.username)
    if not user:
        # Try email as username
        user = user_repo.get_by_email(login_data.username)
    
    # Check if user exists and password is correct
    if not user or not verify_password(login_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for username: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    # Create access token
    access_token = create_access_token(
        subject=user.id,
        data={"role": user.role.value, "username": user.username},
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(subject=user.id)
    
    logger.info(f"User logged in: {user.email} (ID: {user.id})")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    user_repo: UserRepository = Depends(get_user_repository),
) -> Any:
    """
    Refresh access token.
    
    Args:
        refresh_data: Refresh token data
        user_repo: User repository
        
    Returns:
        Token: New access and refresh tokens
        
    Raises:
        HTTPException: If token refresh fails
    """
    try:
        # Decode the refresh token
        payload = decode_token(refresh_data.refresh_token)
        
        # Check if it's a refresh token
        if payload.get("type") != "refresh":
            logger.warning("Invalid token type for refresh")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token payload missing 'sub' field")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user = user_repo.get_by_id(int(user_id))
        if not user:
            logger.warning(f"User with ID {user_id} not found during token refresh")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Token refresh attempt for inactive user: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )
        
        # Create new access token
        access_token = create_access_token(
            subject=user.id,
            data={"role": user.role.value, "username": user.username},
        )
        
        # Create new refresh token
        refresh_token = create_refresh_token(subject=user.id)
        
        logger.info(f"Token refreshed for user: {user.email} (ID: {user.id})")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    except HTTPException:
        # Re-raise HTTPExceptions from decode_token
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
