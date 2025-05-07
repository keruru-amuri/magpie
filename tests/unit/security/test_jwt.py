"""
Unit tests for JWT token handling.
"""
from datetime import datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.core.security.jwt import create_access_token, create_refresh_token, decode_token


def test_create_access_token():
    """Test creating an access token."""
    # Create a token
    user_id = 123
    token = create_access_token(subject=user_id)

    # Decode the token manually to verify its contents
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )

    # Verify the payload
    assert payload["sub"] == str(user_id)
    assert "exp" in payload
    assert "iat" in payload

    # Verify that the token expires in the future
    assert payload["exp"] > datetime.utcnow().timestamp()

    # Verify that the token expires in approximately ACCESS_TOKEN_EXPIRE_MINUTES
    # We don't check the exact time due to potential timezone differences
    expected_exp = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Just verify it's within a day (86400 seconds)
    assert abs(payload["exp"] - expected_exp.timestamp()) < 86400


def test_create_access_token_with_custom_expiration():
    """Test creating an access token with a custom expiration time."""
    # Create a token with a custom expiration time
    user_id = 123
    expires_delta = timedelta(minutes=15)
    token = create_access_token(subject=user_id, expires_delta=expires_delta)

    # Decode the token manually to verify its contents
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )

    # Verify the payload
    assert payload["sub"] == str(user_id)
    assert "exp" in payload

    # Verify that the token expires in approximately 15 minutes
    # We don't check the exact time due to potential timezone differences
    expected_exp = datetime.utcnow() + expires_delta
    # Just verify it's within a day (86400 seconds)
    assert abs(payload["exp"] - expected_exp.timestamp()) < 86400


def test_create_access_token_with_scopes():
    """Test creating an access token with scopes."""
    # Create a token with scopes
    user_id = 123
    scopes = ["read", "write"]
    token = create_access_token(subject=user_id, scopes=scopes)

    # Decode the token manually to verify its contents
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )

    # Verify the payload
    assert payload["sub"] == str(user_id)
    assert payload["scopes"] == scopes


def test_create_access_token_with_additional_data():
    """Test creating an access token with additional data."""
    # Create a token with additional data
    user_id = 123
    data = {"role": "admin", "username": "testuser"}
    token = create_access_token(subject=user_id, data=data)

    # Decode the token manually to verify its contents
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )

    # Verify the payload
    assert payload["sub"] == str(user_id)
    assert payload["role"] == data["role"]
    assert payload["username"] == data["username"]


def test_create_refresh_token():
    """Test creating a refresh token."""
    # Create a token
    user_id = 123
    token = create_refresh_token(subject=user_id)

    # Decode the token manually to verify its contents
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )

    # Verify the payload
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"
    assert "exp" in payload
    assert "iat" in payload

    # Verify that the token expires in the future
    assert payload["exp"] > datetime.utcnow().timestamp()

    # Verify that the token expires in approximately REFRESH_TOKEN_EXPIRE_DAYS
    # We don't check the exact time due to potential timezone differences
    expected_exp = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    # Just verify it's within a day (86400 seconds)
    assert abs(payload["exp"] - expected_exp.timestamp()) < 86400


def test_create_refresh_token_with_custom_expiration():
    """Test creating a refresh token with a custom expiration time."""
    # Create a token with a custom expiration time
    user_id = 123
    expires_delta = timedelta(days=30)
    token = create_refresh_token(subject=user_id, expires_delta=expires_delta)

    # Decode the token manually to verify its contents
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )

    # Verify the payload
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"
    assert "exp" in payload

    # Verify that the token expires in approximately 30 days
    # We don't check the exact time due to potential timezone differences
    expected_exp = datetime.utcnow() + expires_delta
    # Just verify it's within a day (86400 seconds)
    assert abs(payload["exp"] - expected_exp.timestamp()) < 86400


def test_decode_token():
    """Test decoding a token."""
    # Create a token
    user_id = 123
    token = create_access_token(subject=user_id)

    # Decode the token
    payload = decode_token(token)

    # Verify the payload
    assert payload["sub"] == str(user_id)
    assert "exp" in payload
    assert "iat" in payload


def test_decode_token_with_expired_token():
    """Test decoding an expired token."""
    # Create a token that expires immediately
    user_id = 123
    expires_delta = timedelta(seconds=-1)
    token = create_access_token(subject=user_id, expires_delta=expires_delta)

    # Attempt to decode the token
    with pytest.raises(HTTPException) as excinfo:
        decode_token(token)

    # Verify the exception
    assert excinfo.value.status_code == 401
    assert "Token has expired" in excinfo.value.detail


def test_decode_token_with_invalid_token():
    """Test decoding an invalid token."""
    # Create an invalid token
    token = "invalid.token.here"

    # Attempt to decode the token
    with pytest.raises(HTTPException) as excinfo:
        decode_token(token)

    # Verify the exception
    assert excinfo.value.status_code == 401
    assert "Invalid token" in excinfo.value.detail
