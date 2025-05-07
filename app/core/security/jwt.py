"""
JWT token generation and validation utilities for the MAGPIE platform.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

import jwt
from fastapi import HTTPException, status

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


def create_access_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None,
    scopes: Optional[list] = None,
    data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: Subject of the token (usually user ID)
        expires_delta: Token expiration time
        scopes: Token scopes (permissions)
        data: Additional data to include in the token
        
    Returns:
        str: JWT token
    """
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Create token payload
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.utcnow(),
    }
    
    # Add scopes if provided
    if scopes:
        to_encode["scopes"] = scopes
    
    # Add additional data if provided
    if data:
        to_encode.update(data)
    
    # Encode the token
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token",
        )


def create_refresh_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: Subject of the token (usually user ID)
        expires_delta: Token expiration time
        
    Returns:
        str: JWT token
    """
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    # Create token payload
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.utcnow(),
        "type": "refresh",
    }
    
    # Encode the token
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating refresh token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create refresh token",
        )


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode a JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        Dict[str, Any]: Token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Decode the token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
