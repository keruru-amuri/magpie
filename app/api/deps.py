"""Dependency injection for API endpoints."""

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

# OAuth2 token URL (will be implemented in authentication module)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


# Placeholder for database session dependency
def get_db() -> Generator:
    """
    Get database session.
    
    This is a placeholder that will be implemented when the database is set up.
    """
    try:
        # This will be replaced with actual database session
        db = None
        yield db
    finally:
        # Close the database session
        if db is not None:
            pass  # db.close()


# Placeholder for current user dependency
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get the current authenticated user.
    
    This is a placeholder that will be implemented when authentication is set up.
    """
    # This will be replaced with actual user authentication logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not implemented yet",
    )


# Placeholder for current active user dependency
async def get_current_active_user(current_user = Depends(get_current_user)):
    """
    Get the current active user.
    
    This is a placeholder that will be implemented when authentication is set up.
    """
    # This will be replaced with actual user active check
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not implemented yet",
    )
