"""
Test configuration for authentication tests.

This module provides fixtures and configuration for testing the authentication system.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db.connection import Base
from app.core.security import get_password_hash
from app.main import app
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from tests.mocks.redis_mock import RedisMockManager


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


@pytest.fixture(scope="module", autouse=True)
def setup_redis_mock():
    """
    Set up Redis mock for all tests in this module.

    This fixture is automatically used for all tests in the module.
    """
    # Enable Redis mock
    RedisMockManager.enable_redis_mock()

    yield

    # Disable Redis mock
    RedisMockManager.disable_redis_mock()


@pytest.fixture
def fake_redis():
    """
    Get fake Redis instance.

    Returns:
        FakeRedis: Fake Redis instance
    """
    redis = RedisMockManager.get_fake_redis()

    # Reset Redis data before each test
    redis.flushall()

    return redis


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
def auth_client(db_session):
    """
    Create a test client with a database session and test users.
    """
    # Ensure we're in testing environment
    from app.core.config import settings, EnvironmentType
    settings.ENVIRONMENT = EnvironmentType.TESTING
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

    # Create a test user for login tests
    test_user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("Password123!"),
        full_name="Test User",
        role=UserRole.TECHNICIAN,
        is_active=True,
    )
    db_session.add(test_user)

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

    # Create an inactive user
    inactive_user = User(
        email="inactive@example.com",
        username="inactive",
        hashed_password=get_password_hash("Password123!"),
        full_name="Inactive User",
        role=UserRole.TECHNICIAN,
        is_active=False,
    )
    db_session.add(inactive_user)

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


@pytest.fixture
def admin_token(auth_client):
    """
    Get an admin user token.

    Args:
        auth_client: Test client

    Returns:
        str: JWT token
    """
    # Login as admin
    response = auth_client.post(
        "/api/v1/auth/login/access-token",
        json={"username": "admin", "password": "Password123!"}
    )

    # Return token
    return response.json()["access_token"]


@pytest.fixture
def user_token(auth_client):
    """
    Get a regular user token.

    Args:
        auth_client: Test client

    Returns:
        str: JWT token
    """
    # Login as regular user
    response = auth_client.post(
        "/api/v1/auth/login/access-token",
        json={"username": "user", "password": "Password123!"}
    )

    # Return token
    return response.json()["access_token"]


@pytest.fixture
def manager_token(auth_client):
    """
    Get a manager user token.

    Args:
        auth_client: Test client

    Returns:
        str: JWT token
    """
    # Login as manager
    response = auth_client.post(
        "/api/v1/auth/login/access-token",
        json={"username": "manager", "password": "Password123!"}
    )

    # Return token
    return response.json()["access_token"]
