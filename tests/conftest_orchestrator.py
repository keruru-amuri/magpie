"""
Test configuration for the orchestrator component.

This module provides fixtures and configuration for testing the orchestrator component.
"""
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.models.conversation import AgentType
from app.models.orchestrator import RequestClassification, OrchestratorResponse
from app.core.orchestrator import Orchestrator
from app.main import app
from app.core.db.connection import Base
from app.api.api_v1.endpoints.orchestrator import get_orchestrator


class MockLLMService:
    """
    Mock LLM service for testing.
    """

    async def generate_chat_completion(self, messages, model=None, temperature=None, max_tokens=None):
        """
        Generate a mock chat completion.

        Args:
            messages: List of messages
            model: Optional model to use
            temperature: Optional temperature
            max_tokens: Optional max tokens

        Returns:
            dict: Mock chat completion response
        """
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "This is a mock response for testing"
                    }
                }
            ]
        }

    async def classify_request(self, query, options=None):
        """
        Classify a request.

        Args:
            query: Query to classify
            options: Optional classification options

        Returns:
            dict: Mock classification response
        """
        return {
            "agent_type": "documentation",
            "confidence": 0.9,
            "reasoning": "This is a mock classification for testing"
        }


@pytest.fixture
def mock_llm_service():
    """
    Create a mock LLM service.

    Returns:
        MockLLMService: Mock LLM service
    """
    return MockLLMService()


@pytest.fixture
def mock_agent_repository():
    """
    Create a mock agent repository.

    Returns:
        MagicMock: Mock agent repository
    """
    mock_repo = MagicMock()

    # Mock agent configurations
    doc_config = MagicMock()
    doc_config.id = 1
    doc_config.agent_type = AgentType.DOCUMENTATION
    doc_config.name = "Documentation Assistant"
    doc_config.description = "Helps find information in technical documentation"
    doc_config.meta_data = {
        "is_default": True,
        "capabilities": [
            {
                "name": "Documentation Search",
                "description": "Find and extract information from technical documentation",
                "keywords": ["manual", "document", "find", "search", "information"],
                "examples": ["Where can I find information about landing gear maintenance?"]
            }
        ]
    }

    ts_config = MagicMock()
    ts_config.id = 2
    ts_config.agent_type = AgentType.TROUBLESHOOTING
    ts_config.name = "Troubleshooting Advisor"
    ts_config.description = "Helps diagnose and resolve issues"
    ts_config.meta_data = {
        "is_default": True,
        "capabilities": [
            {
                "name": "Problem Diagnosis",
                "description": "Diagnose issues based on symptoms",
                "keywords": ["problem", "issue", "error", "diagnose", "troubleshoot"],
                "examples": ["The hydraulic system is showing low pressure, what could be the cause?"]
            }
        ]
    }

    maint_config = MagicMock()
    maint_config.id = 3
    maint_config.agent_type = AgentType.MAINTENANCE
    maint_config.name = "Maintenance Procedure Generator"
    maint_config.description = "Creates maintenance procedures"
    maint_config.meta_data = {
        "is_default": True,
        "capabilities": [
            {
                "name": "Procedure Generation",
                "description": "Create maintenance procedures",
                "keywords": ["procedure", "steps", "maintenance", "how to"],
                "examples": ["What are the steps to replace the fuel filter?"]
            }
        ]
    }

    # Configure mock repository to return appropriate configurations
    mock_repo.get_by_agent_type.side_effect = lambda agent_type, active_only=True: {
        AgentType.DOCUMENTATION: [doc_config],
        AgentType.TROUBLESHOOTING: [ts_config],
        AgentType.MAINTENANCE: [maint_config]
    }.get(agent_type, [])

    return mock_repo


@pytest.fixture
def mock_conversation_repository():
    """
    Create a mock conversation repository.

    Returns:
        MagicMock: Mock conversation repository
    """
    mock_repo = MagicMock()

    # Mock messages
    user_message = MagicMock()
    user_message.role = "user"
    user_message.content = "Test message"
    user_message.timestamp = "2023-01-01T00:00:00"
    user_message.metadata = {}

    assistant_message = MagicMock()
    assistant_message.role = "assistant"
    assistant_message.content = "Test response"
    assistant_message.timestamp = "2023-01-01T00:00:01"
    assistant_message.metadata = {"agent_type": "documentation"}

    # Configure mock repository to return appropriate messages
    mock_repo.get_messages.return_value = [user_message, assistant_message]

    # Add delete_conversation method
    mock_repo.delete_conversation = MagicMock(return_value=True)

    return mock_repo


@pytest.fixture(scope="function")
def test_session():
    """
    Create a test database session.

    Returns:
        Session: SQLAlchemy session
    """
    # Create in-memory SQLite database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    # Create tables
    Base.metadata.create_all(engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
async def async_test_session():
    """
    Create an async test database session.

    Returns:
        AsyncSession: SQLAlchemy async session
    """
    # Create in-memory SQLite database for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    session = async_session()

    yield session

    # Cleanup
    await session.close()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mock_orchestrator():
    """
    Create a mock orchestrator.

    Returns:
        MagicMock: Mock orchestrator
    """
    # Create a mock orchestrator
    mock_orchestrator = MagicMock()

    # Mock process_request method
    mock_orchestrator.process_request = AsyncMock(return_value=OrchestratorResponse(
        response="This is a test response",
        agent_type=AgentType.DOCUMENTATION,
        agent_name="Documentation Assistant",
        confidence=0.9,
        conversation_id="test-conversation-id"
    ))

    # Mock initialize method
    mock_orchestrator.initialize = AsyncMock()

    # Mock classifier
    mock_classifier = MagicMock()
    mock_classifier.classify_request = AsyncMock(return_value=RequestClassification(
        agent_type=AgentType.DOCUMENTATION,
        confidence=0.9,
        reasoning="This is a documentation request",
        requires_followup=False,
        requires_multiple_agents=False
    ))
    mock_orchestrator.classifier = mock_classifier

    # Mock router
    mock_router = MagicMock()

    # Create a RequestClassification object for the RoutingResult
    classification = RequestClassification(
        agent_type=AgentType.DOCUMENTATION,
        confidence=0.9,
        reasoning="This is a documentation request"
    )

    # Create a RoutingResult object
    routing_result = MagicMock()
    routing_result.agent_type = AgentType.DOCUMENTATION
    routing_result.agent_config_id = 1
    routing_result.classification = classification
    routing_result.fallback_agent_config_id = None
    routing_result.requires_followup = False
    routing_result.requires_multiple_agents = False
    routing_result.additional_agent_types = None

    # Mock the route_request method to return the RoutingResult
    mock_router.route_request = AsyncMock(return_value=routing_result)
    mock_router.clear_routing_history = MagicMock()
    mock_orchestrator.router = mock_router

    # Mock conversation repository
    from datetime import datetime

    # Create proper message objects with datetime objects for timestamps
    user_message = MagicMock()
    user_message.role = "user"
    user_message.content = "Test message"
    user_message.timestamp = datetime(2023, 1, 1, 0, 0, 0)
    user_message.metadata = {}

    assistant_message = MagicMock()
    assistant_message.role = "assistant"
    assistant_message.content = "Test response"
    assistant_message.timestamp = datetime(2023, 1, 1, 0, 0, 1)
    assistant_message.metadata = {"agent_type": "documentation"}

    mock_conversation_repository = MagicMock()
    mock_conversation_repository.get_messages = MagicMock(return_value=[
        user_message,
        assistant_message
    ])
    mock_conversation_repository.delete_conversation = MagicMock(return_value=True)
    mock_orchestrator.conversation_repository = mock_conversation_repository

    # Mock _get_conversation_history method
    mock_orchestrator._get_conversation_history = AsyncMock(return_value=[])

    return mock_orchestrator


@pytest.fixture
def orchestrator_client(mock_orchestrator, test_session):
    """
    Create a test client with a mock orchestrator.

    Args:
        mock_orchestrator: Mock orchestrator
        test_session: Test database session

    Returns:
        TestClient: Test client
    """
    # Create an async function that returns the mock orchestrator
    async def override_get_orchestrator():
        return mock_orchestrator

    # Create a function to override the get_db dependency
    def override_get_db():
        try:
            yield test_session
        finally:
            pass

    # Override the dependencies
    from app.api.deps import get_db
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_orchestrator] = override_get_orchestrator

    # Set environment to testing to disable rate limiting
    import os
    os.environ["ENVIRONMENT"] = "testing"

    # Create a test client
    client = TestClient(app)

    yield client

    # Clear the dependency override
    app.dependency_overrides.clear()


@pytest.fixture
async def async_orchestrator_client(mock_orchestrator, async_test_session):
    """
    Create an async test client with a mock orchestrator.

    Args:
        mock_orchestrator: Mock orchestrator
        async_test_session: Async test database session

    Returns:
        AsyncClient: Async test client
    """
    # Create an async function that returns the mock orchestrator
    async def override_get_orchestrator():
        return mock_orchestrator

    # Create an async function to override the get_db dependency
    async def override_get_db():
        try:
            yield async_test_session
        finally:
            pass

    # Override the dependencies
    from app.api.deps import get_db
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_orchestrator] = override_get_orchestrator

    # Set environment to testing to disable rate limiting
    import os
    os.environ["ENVIRONMENT"] = "testing"

    # Create an async test client
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Clear the dependency override
    app.dependency_overrides.clear()
