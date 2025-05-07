"""
User management endpoints for the MAGPIE platform.
"""
import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import (
    get_current_active_user,
    get_current_superuser,
    get_user_repository,
)
from app.core.security import Permission, get_password_hash, require_permissions
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import UserResponse, UserUpdate

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user.
    
    Args:
        current_user: Current user
        
    Returns:
        UserResponse: Current user
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> Any:
    """
    Update current user.
    
    Args:
        user_in: User update data
        current_user: Current user
        user_repo: User repository
        
    Returns:
        UserResponse: Updated user
        
    Raises:
        HTTPException: If update fails
    """
    # Check if email is being updated and already exists
    if user_in.email and user_in.email != current_user.email:
        user = user_repo.get_by_email(user_in.email)
        if user and user.id != current_user.id:
            logger.warning(
                f"User {current_user.id} attempted to update email to existing email: {user_in.email}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    
    # Check if username is being updated and already exists
    if user_in.username and user_in.username != current_user.username:
        user = user_repo.get_by_username(user_in.username)
        if user and user.id != current_user.id:
            logger.warning(
                f"User {current_user.id} attempted to update username to existing username: {user_in.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
    
    # Prepare update data
    update_data = user_in.model_dump(exclude_unset=True)
    
    # Hash password if provided
    if user_in.password:
        update_data["hashed_password"] = get_password_hash(user_in.password)
        update_data.pop("password", None)
    
    # Don't allow regular users to update their role or superuser status
    update_data.pop("role", None)
    update_data.pop("is_superuser", None)
    
    # Update user
    updated_user = user_repo.update(current_user.id, update_data)
    if not updated_user:
        logger.error(f"Failed to update user: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )
    
    logger.info(f"User updated: {updated_user.email} (ID: {updated_user.id})")
    return updated_user


@router.get("", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_permissions(Permission.VIEW_USERS)),
    user_repo: UserRepository = Depends(get_user_repository),
) -> Any:
    """
    Get all users.
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        current_user: Current user with VIEW_USERS permission
        user_repo: User repository
        
    Returns:
        List[UserResponse]: List of users
    """
    users = user_repo.get_multi(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int,
    current_user: User = Depends(require_permissions(Permission.VIEW_USERS)),
    user_repo: UserRepository = Depends(get_user_repository),
) -> Any:
    """
    Get user by ID.
    
    Args:
        user_id: User ID
        current_user: Current user with VIEW_USERS permission
        user_repo: User repository
        
    Returns:
        UserResponse: User
        
    Raises:
        HTTPException: If user not found
    """
    user = user_repo.get_by_id(user_id)
    if not user:
        logger.warning(f"User with ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(require_permissions(Permission.MANAGE_USERS)),
    user_repo: UserRepository = Depends(get_user_repository),
) -> Any:
    """
    Update user.
    
    Args:
        user_id: User ID
        user_in: User update data
        current_user: Current user with MANAGE_USERS permission
        user_repo: User repository
        
    Returns:
        UserResponse: Updated user
        
    Raises:
        HTTPException: If update fails
    """
    # Get user to update
    user = user_repo.get_by_id(user_id)
    if not user:
        logger.warning(f"User with ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if email is being updated and already exists
    if user_in.email and user_in.email != user.email:
        existing_user = user_repo.get_by_email(user_in.email)
        if existing_user and existing_user.id != user_id:
            logger.warning(
                f"Admin {current_user.id} attempted to update user {user_id} email to existing email: {user_in.email}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    
    # Check if username is being updated and already exists
    if user_in.username and user_in.username != user.username:
        existing_user = user_repo.get_by_username(user_in.username)
        if existing_user and existing_user.id != user_id:
            logger.warning(
                f"Admin {current_user.id} attempted to update user {user_id} username to existing username: {user_in.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
    
    # Prepare update data
    update_data = user_in.model_dump(exclude_unset=True)
    
    # Hash password if provided
    if user_in.password:
        update_data["hashed_password"] = get_password_hash(user_in.password)
        update_data.pop("password", None)
    
    # Only superusers can update superuser status
    if "is_superuser" in update_data and not current_user.is_superuser:
        logger.warning(
            f"Non-superuser {current_user.id} attempted to update superuser status of user {user_id}"
        )
        update_data.pop("is_superuser")
    
    # Update user
    updated_user = user_repo.update(user_id, update_data)
    if not updated_user:
        logger.error(f"Failed to update user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )
    
    logger.info(f"User {user_id} updated by admin {current_user.id}")
    return updated_user


@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    user_repo: UserRepository = Depends(get_user_repository),
) -> Any:
    """
    Delete user.
    
    Args:
        user_id: User ID
        current_user: Current superuser
        user_repo: User repository
        
    Returns:
        UserResponse: Deleted user
        
    Raises:
        HTTPException: If deletion fails
    """
    # Get user to delete
    user = user_repo.get_by_id(user_id)
    if not user:
        logger.warning(f"User with ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Prevent self-deletion
    if user_id == current_user.id:
        logger.warning(f"Superuser {current_user.id} attempted to delete themselves")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )
    
    # Delete user
    success = user_repo.delete_by_id(user_id)
    if not success:
        logger.error(f"Failed to delete user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )
    
    logger.info(f"User {user_id} deleted by superuser {current_user.id}")
    return user
