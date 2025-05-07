"""
Integration tests for user endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db.connection import Base
from app.core.security import get_password_hash
from app.main import app
from app.models.user import User, UserRole
from app.repositories.user import UserRepository


# Create an in-memory SQLite database for testing
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create the database tables
Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session():
    """
    Create a fresh database session for each test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    # Create tables
    Base.metadata.create_all(bind=connection)
    
    yield session
    
    # Rollback the transaction and close the connection
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """
    Create a test client with a database session.
    """
    # Create a test admin user
    admin_user = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("Password123!"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        is_superuser=True,
    )
    db_session.add(admin_user)
    
    # Create a test regular user
    regular_user = User(
        email="user@example.com",
        username="user",
        hashed_password=get_password_hash("Password123!"),
        full_name="Regular User",
        role=UserRole.TECHNICIAN,
        is_active=True,
    )
    db_session.add(regular_user)
    
    # Create a test manager user
    manager_user = User(
        email="manager@example.com",
        username="manager",
        hashed_password=get_password_hash("Password123!"),
        full_name="Manager User",
        role=UserRole.MANAGER,
        is_active=True,
    )
    db_session.add(manager_user)
    
    db_session.commit()
    
    # Override the get_db dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Use the test database instead of the real database
    from app.api.deps import get_db
    app.dependency_overrides[get_db] = override_get_db
    
    # Create a test client
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()


def get_token_headers(client, username, password):
    """
    Get token headers for authentication.
    """
    login_data = {
        "username": username,
        "password": password,
    }
    response = client.post("/api/v1/auth/login/access-token", json=login_data)
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_read_current_user(client):
    """Test reading current user."""
    # Get token headers
    headers = get_token_headers(client, "user", "Password123!")
    
    # Get current user
    response = client.get("/api/v1/users/me", headers=headers)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["username"] == "user"
    assert data["full_name"] == "Regular User"
    assert data["role"] == "technician"
    assert data["is_active"] is True
    assert data["is_superuser"] is False


def test_update_current_user(client, db_session):
    """Test updating current user."""
    # Get token headers
    headers = get_token_headers(client, "user", "Password123!")
    
    # Update data
    update_data = {
        "full_name": "Updated User",
    }
    
    # Update current user
    response = client.put("/api/v1/users/me", json=update_data, headers=headers)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["username"] == "user"
    assert data["full_name"] == "Updated User"
    assert data["role"] == "technician"
    assert data["is_active"] is True
    assert data["is_superuser"] is False
    
    # Check that the user was updated in the database
    user_repo = UserRepository(session=db_session)
    user = user_repo.get_by_username("user")
    assert user.full_name == "Updated User"


def test_update_current_user_password(client, db_session):
    """Test updating current user password."""
    # Get token headers
    headers = get_token_headers(client, "user", "Password123!")
    
    # Update data
    update_data = {
        "password": "NewPassword123!",
    }
    
    # Update current user
    response = client.put("/api/v1/users/me", json=update_data, headers=headers)
    
    # Check response
    assert response.status_code == 200
    
    # Try to login with the new password
    login_data = {
        "username": "user",
        "password": "NewPassword123!",
    }
    login_response = client.post("/api/v1/auth/login/access-token", json=login_data)
    assert login_response.status_code == 200


def test_read_users(client):
    """Test reading all users."""
    # Get token headers for admin
    headers = get_token_headers(client, "admin", "Password123!")
    
    # Get all users
    response = client.get("/api/v1/users", headers=headers)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3  # admin, user, manager
    
    # Get token headers for manager
    headers = get_token_headers(client, "manager", "Password123!")
    
    # Get all users
    response = client.get("/api/v1/users", headers=headers)
    
    # Check response
    assert response.status_code == 200
    
    # Get token headers for regular user
    headers = get_token_headers(client, "user", "Password123!")
    
    # Get all users
    response = client.get("/api/v1/users", headers=headers)
    
    # Check response
    assert response.status_code == 403  # Forbidden


def test_read_user(client):
    """Test reading a specific user."""
    # Get token headers for admin
    headers = get_token_headers(client, "admin", "Password123!")
    
    # Get user by ID
    response = client.get("/api/v1/users/2", headers=headers)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["username"] == "user"
    
    # Get token headers for regular user
    headers = get_token_headers(client, "user", "Password123!")
    
    # Get user by ID
    response = client.get("/api/v1/users/1", headers=headers)
    
    # Check response
    assert response.status_code == 403  # Forbidden


def test_update_user(client, db_session):
    """Test updating a user."""
    # Get token headers for admin
    headers = get_token_headers(client, "admin", "Password123!")
    
    # Update data
    update_data = {
        "full_name": "Updated Regular User",
        "role": "engineer",
    }
    
    # Update user
    response = client.put("/api/v1/users/2", json=update_data, headers=headers)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["username"] == "user"
    assert data["full_name"] == "Updated Regular User"
    assert data["role"] == "engineer"
    
    # Check that the user was updated in the database
    user_repo = UserRepository(session=db_session)
    user = user_repo.get_by_id(2)
    assert user.full_name == "Updated Regular User"
    assert user.role == UserRole.ENGINEER
    
    # Get token headers for regular user
    headers = get_token_headers(client, "user", "Password123!")
    
    # Update user
    response = client.put("/api/v1/users/1", json=update_data, headers=headers)
    
    # Check response
    assert response.status_code == 403  # Forbidden


def test_delete_user(client, db_session):
    """Test deleting a user."""
    # Get token headers for admin
    headers = get_token_headers(client, "admin", "Password123!")
    
    # Delete user
    response = client.delete("/api/v1/users/2", headers=headers)
    
    # Check response
    assert response.status_code == 200
    
    # Check that the user was deleted from the database
    user_repo = UserRepository(session=db_session)
    user = user_repo.get_by_id(2)
    assert user is None
    
    # Get token headers for manager
    headers = get_token_headers(client, "manager", "Password123!")
    
    # Delete user
    response = client.delete("/api/v1/users/3", headers=headers)
    
    # Check response
    assert response.status_code == 403  # Forbidden
