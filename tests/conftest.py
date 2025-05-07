"""Pytest configuration for MAGPIE platform."""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config import settings
from app.main import app
from app.core.db.connection import Base
from app.models.user import User, UserRole
from app.models.conversation import Conversation, Message, MessageRole, AgentType
from app.models.agent import AgentConfiguration, ModelSize
from tests.db_utils import (
    test_engine,
    test_session,
    override_get_db,
    async_test_engine,
    async_test_session,
    async_override_get_db
)

# Set testing environment variable
os.environ["TESTING"] = "true"

# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]

# Set default event loop policy
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI application."""
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client


@pytest.fixture(scope="session")
def test_environment():
    """Set up test environment variables."""
    # Store original environment
    original_env = os.environ.copy()

    # Set test environment variables
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DEBUG"] = "true"

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="function")
def override_settings():
    """Override settings for testing."""
    original_settings = {
        "ENVIRONMENT": settings.ENVIRONMENT,
        "DEBUG": settings.DEBUG,
        "PROJECT_NAME": settings.PROJECT_NAME,
    }

    # Override settings for testing
    settings.ENVIRONMENT = "testing"
    settings.DEBUG = True
    settings.PROJECT_NAME = "MAGPIE-Test"

    yield settings

    # Restore original settings
    settings.ENVIRONMENT = original_settings["ENVIRONMENT"]
    settings.DEBUG = original_settings["DEBUG"]
    settings.PROJECT_NAME = original_settings["PROJECT_NAME"]


@pytest.fixture(scope="function")
def mock_azure_openai(monkeypatch):
    """Mock Azure OpenAI API calls."""
    class MockAzureOpenAI:
        def __init__(self, *args, **kwargs):
            pass

        def chat_completions(self, *args, **kwargs):
            return {
                "choices": [
                    {
                        "message": {
                            "content": "This is a mock response from Azure OpenAI."
                        }
                    }
                ]
            }

    monkeypatch.setattr("app.services.azure_openai.AzureOpenAI", MockAzureOpenAI)
    return MockAzureOpenAI


@pytest.fixture(scope="session")
def test_db_engine():
    """
    Create SQLAlchemy engine for testing.
    """
    # Use in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")

    # Create tables
    Base.metadata.create_all(engine)

    yield engine

    # Drop tables
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """
    Create SQLAlchemy session for testing.
    """
    # Create session factory
    Session = sessionmaker(bind=test_db_engine)

    # Create session
    session = Session()

    yield session

    # Rollback changes
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def test_user(test_db_session):
    """
    Create test user.
    """
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashedpassword",
        full_name="Test User",
        role=UserRole.ENGINEER
    )
    test_db_session.add(user)
    test_db_session.commit()

    return user


@pytest.fixture(scope="function")
def test_conversation(test_db_session, test_user):
    """
    Create test conversation.
    """
    conversation = Conversation(
        user_id=test_user.id,
        agent_type=AgentType.DOCUMENTATION,
        title="Test Conversation"
    )
    test_db_session.add(conversation)
    test_db_session.commit()

    return conversation


@pytest.fixture(scope="function")
def test_messages(test_db_session, test_conversation):
    """
    Create test messages.
    """
    messages = [
        Message(
            conversation_id=test_conversation.id,
            role=MessageRole.SYSTEM,
            content="System message"
        ),
        Message(
            conversation_id=test_conversation.id,
            role=MessageRole.USER,
            content="User message"
        ),
        Message(
            conversation_id=test_conversation.id,
            role=MessageRole.ASSISTANT,
            content="Assistant message"
        )
    ]
    test_db_session.add_all(messages)
    test_db_session.commit()

    return messages


@pytest.fixture(scope="function")
def test_agent_config(test_db_session):
    """
    Create test agent configuration.
    """
    config = AgentConfiguration(
        name="Test Agent",
        description="Test agent configuration",
        agent_type=AgentType.DOCUMENTATION,
        model_size=ModelSize.MEDIUM,
        temperature=0.7,
        max_tokens=4000,
        system_prompt="You are a helpful assistant."
    )
    test_db_session.add(config)
    test_db_session.commit()

    return config
