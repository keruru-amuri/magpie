"""
Integration tests for authentication endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from app.models.user import UserRole
from app.repositories.user import UserRepository
from tests.conftest_auth import auth_client, db_session, fake_redis


def test_register_user(auth_client, db_session):
    """Test user registration."""
    # Test data
    user_data = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "Password123!",
        "full_name": "New User",
        "role": "technician",
    }

    # Register a new user
    response = auth_client.post("/api/v1/auth/register", json=user_data)

    # Check response
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert data["full_name"] == user_data["full_name"]
    assert data["role"] == user_data["role"]
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data

    # Check that the user was created in the database
    user_repo = UserRepository(session=db_session)
    user = user_repo.get_by_email(user_data["email"])
    assert user is not None
    assert user.email == user_data["email"]
    assert user.username == user_data["username"]
    assert user.full_name == user_data["full_name"]
    assert user.role == UserRole.TECHNICIAN
    assert user.is_active is True


def test_register_user_duplicate_email(auth_client, db_session):
    """Test user registration with duplicate email."""
    # Test data
    user_data = {
        "email": "test@example.com",  # Already exists
        "username": "newuser",
        "password": "Password123!",
        "full_name": "New User",
        "role": "technician",
    }

    # Register a new user
    response = auth_client.post("/api/v1/auth/register", json=user_data)

    # Check response
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "email already exists" in data["detail"].lower()


def test_register_user_duplicate_username(auth_client, db_session):
    """Test user registration with duplicate username."""
    # Test data
    user_data = {
        "email": "newuser@example.com",
        "username": "testuser",  # Already exists
        "password": "Password123!",
        "full_name": "New User",
        "role": "technician",
    }

    # Register a new user
    response = auth_client.post("/api/v1/auth/register", json=user_data)

    # Check response
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "username already exists" in data["detail"].lower()


def test_login_user(auth_client):
    """Test user login."""
    # Test data
    login_data = {
        "username": "testuser",
        "password": "Password123!",
    }

    # Login
    response = auth_client.post("/api/v1/auth/login/access-token", json=login_data)

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_user_invalid_credentials(auth_client):
    """Test user login with invalid credentials."""
    # Test data
    login_data = {
        "username": "testuser",
        "password": "WrongPassword123!",
    }

    # Login
    response = auth_client.post("/api/v1/auth/login/access-token", json=login_data)

    # Check response
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "incorrect username or password" in data["detail"].lower()


def test_refresh_token(auth_client):
    """Test token refresh."""
    # First, login to get tokens
    login_data = {
        "username": "testuser",
        "password": "Password123!",
    }
    login_response = auth_client.post("/api/v1/auth/login/access-token", json=login_data)
    login_data = login_response.json()

    # Test data
    refresh_data = {
        "refresh_token": login_data["refresh_token"],
    }

    # Refresh token
    response = auth_client.post("/api/v1/auth/refresh-token", json=refresh_data)

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["access_token"] != login_data["access_token"]
    assert data["refresh_token"] != login_data["refresh_token"]
