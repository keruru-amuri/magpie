"""
Test configuration for agent components.

This module provides fixtures and configuration for testing agent components.
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

from app.models.conversation import AgentType, Message, MessageRole
from app.models.agent import AgentConfiguration, ModelSize
from app.core.db.connection import Base
from app.main import app
from app.services.llm_service import LLMService


class MockDocumentationService:
    """
    Mock documentation service for testing.
    """

    async def search_documents(self, query, filters=None):
        """
        Search documents with a mock implementation.

        Args:
            query: Search query
            filters: Optional filters

        Returns:
            List[Dict]: List of document search results
        """
        return [
            {
                "id": "doc-001",
                "title": "Test Document 1",
                "content": "This is test content for document 1",
                "relevance": 0.9,
                "source": "Test Source",
                "url": "https://example.com/doc1"
            },
            {
                "id": "doc-002",
                "title": "Test Document 2",
                "content": "This is test content for document 2",
                "relevance": 0.8,
                "source": "Test Source",
                "url": "https://example.com/doc2"
            }
        ]

    async def get_document(self, doc_id):
        """
        Get a document with a mock implementation.

        Args:
            doc_id: Document ID

        Returns:
            Dict: Document details
        """
        return {
            "id": doc_id,
            "title": f"Test Document {doc_id}",
            "content": f"This is test content for document {doc_id}",
            "source": "Test Source",
            "url": f"https://example.com/{doc_id}",
            "metadata": {
                "aircraft_type": "Boeing 737",
                "system": "Hydraulic",
                "document_type": "Manual"
            }
        }


class MockTroubleshootingService:
    """
    Mock troubleshooting service for testing.
    """

    async def get_systems(self):
        """
        Get available systems with a mock implementation.

        Returns:
            List[Dict]: List of available systems
        """
        return [
            {
                "id": "system-001",
                "name": "Hydraulic System",
                "description": "Aircraft hydraulic system"
            },
            {
                "id": "system-002",
                "name": "Electrical System",
                "description": "Aircraft electrical system"
            },
            {
                "id": "system-003",
                "name": "Fuel System",
                "description": "Aircraft fuel system"
            }
        ]

    async def get_symptoms(self, system_id):
        """
        Get symptoms for a system with a mock implementation.

        Args:
            system_id: System ID

        Returns:
            List[Dict]: List of symptoms
        """
        return [
            {
                "id": "symptom-001",
                "description": "Low pressure",
                "system_id": system_id
            },
            {
                "id": "symptom-002",
                "description": "Unusual noise",
                "system_id": system_id
            },
            {
                "id": "symptom-003",
                "description": "Fluid leakage",
                "system_id": system_id
            }
        ]

    async def diagnose_issue(self, system, symptoms, context=None):
        """
        Diagnose an issue with a mock implementation.

        Args:
            system: System ID
            symptoms: List of symptoms
            context: Optional context

        Returns:
            Dict: Diagnosis result
        """
        return {
            "request": {
                "system": system,
                "symptoms": symptoms,
                "context": context or ""
            },
            "analysis": {
                "potential_causes": [
                    {
                        "id": "cause-001",
                        "description": "Faulty component",
                        "probability": 0.75,
                        "evidence": "Based on the symptoms provided, this is likely caused by a faulty component."
                    },
                    {
                        "id": "cause-002",
                        "description": "Improper maintenance",
                        "probability": 0.45,
                        "evidence": "The symptoms may also indicate improper maintenance procedures."
                    }
                ],
                "recommended_actions": [
                    {
                        "id": "action-001",
                        "description": "Inspect component",
                        "priority": "high",
                        "tools_required": ["Inspection tool", "Pressure gauge"],
                        "estimated_time": "30 minutes"
                    },
                    {
                        "id": "action-002",
                        "description": "Replace component if faulty",
                        "priority": "medium",
                        "tools_required": ["Replacement part", "Wrench set"],
                        "estimated_time": "2 hours"
                    }
                ],
                "safety_notes": [
                    "Ensure system is depressurized before inspection",
                    "Follow proper lockout/tagout procedures"
                ]
            }
        }


class MockMaintenanceService:
    """
    Mock maintenance service for testing.
    """

    async def get_aircraft_types(self):
        """
        Get available aircraft types with a mock implementation.

        Returns:
            List[Dict]: List of available aircraft types
        """
        return [
            {
                "id": "aircraft-001",
                "name": "Boeing 737",
                "description": "Boeing 737 aircraft"
            },
            {
                "id": "aircraft-002",
                "name": "Airbus A320",
                "description": "Airbus A320 aircraft"
            }
        ]

    async def get_systems(self, aircraft_id):
        """
        Get systems for an aircraft type with a mock implementation.

        Args:
            aircraft_id: Aircraft type ID

        Returns:
            List[Dict]: List of systems
        """
        return [
            {
                "id": "system-001",
                "name": "Hydraulic System",
                "description": "Aircraft hydraulic system",
                "aircraft_id": aircraft_id
            },
            {
                "id": "system-002",
                "name": "Electrical System",
                "description": "Aircraft electrical system",
                "aircraft_id": aircraft_id
            }
        ]

    async def get_procedure_types(self, aircraft_id, system_id):
        """
        Get procedure types for a system with a mock implementation.

        Args:
            aircraft_id: Aircraft type ID
            system_id: System ID

        Returns:
            List[Dict]: List of procedure types
        """
        return [
            {
                "id": "procedure-type-001",
                "name": "Inspection",
                "description": "Inspection procedure"
            },
            {
                "id": "procedure-type-002",
                "name": "Replacement",
                "description": "Replacement procedure"
            },
            {
                "id": "procedure-type-003",
                "name": "Troubleshooting",
                "description": "Troubleshooting procedure"
            }
        ]

    async def generate_procedure(self, aircraft_type, system, procedure_type, parameters=None):
        """
        Generate a maintenance procedure with a mock implementation.

        Args:
            aircraft_type: Aircraft type ID
            system: System ID
            procedure_type: Procedure type ID
            parameters: Optional parameters

        Returns:
            Dict: Generated procedure
        """
        return {
            "request": {
                "aircraft_type": aircraft_type,
                "system": system,
                "procedure_type": procedure_type,
                "parameters": parameters or {}
            },
            "procedure": {
                "title": f"{procedure_type} Procedure for {system} on {aircraft_type}",
                "description": f"This procedure provides steps for {procedure_type} of the {system} on {aircraft_type} aircraft.",
                "prerequisites": [
                    "Ensure aircraft is properly grounded",
                    "Obtain necessary tools and equipment",
                    "Review relevant technical documentation"
                ],
                "safety_precautions": [
                    "Follow all safety protocols",
                    "Use appropriate personal protective equipment",
                    "Ensure system is de-energized before beginning work"
                ],
                "tools_required": [
                    "Standard tool kit",
                    "Specialized tools as needed",
                    "Calibrated measurement equipment"
                ],
                "steps": [
                    {
                        "step_number": 1,
                        "description": "Prepare the work area",
                        "details": "Clear the work area and ensure proper lighting and ventilation."
                    },
                    {
                        "step_number": 2,
                        "description": "Access the system",
                        "details": "Remove access panels or covers as necessary."
                    },
                    {
                        "step_number": 3,
                        "description": "Perform the procedure",
                        "details": "Follow the specific steps for the selected procedure type."
                    },
                    {
                        "step_number": 4,
                        "description": "Verify completion",
                        "details": "Ensure all work has been completed correctly."
                    },
                    {
                        "step_number": 5,
                        "description": "Close up and document",
                        "details": "Replace all access panels and document the work performed."
                    }
                ],
                "verification": [
                    "Perform functional test as required",
                    "Verify proper operation of the system",
                    "Document all test results"
                ],
                "references": [
                    {
                        "title": "Aircraft Maintenance Manual",
                        "section": "Chapter 5, Section 3",
                        "document_id": "AMM-001"
                    },
                    {
                        "title": "Component Maintenance Manual",
                        "section": "Chapter 2, Section 1",
                        "document_id": "CMM-001"
                    }
                ]
            }
        }


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

    async def generate_completion(self, prompt_template, variables, model=None, temperature=None, max_tokens=None):
        """
        Generate a mock completion.

        Args:
            prompt_template: Prompt template
            variables: Variables for the template
            model: Optional model to use
            temperature: Optional temperature
            max_tokens: Optional max tokens

        Returns:
            dict: Mock completion response
        """
        return {
            "content": "This is a mock response for testing"
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
def mock_documentation_service():
    """
    Create a mock documentation service.

    Returns:
        MockDocumentationService: Mock documentation service
    """
    return MockDocumentationService()


@pytest.fixture
def mock_troubleshooting_service():
    """
    Create a mock troubleshooting service.

    Returns:
        MockTroubleshootingService: Mock troubleshooting service
    """
    return MockTroubleshootingService()


@pytest.fixture
def mock_maintenance_service():
    """
    Create a mock maintenance service.

    Returns:
        MockMaintenanceService: Mock maintenance service
    """
    return MockMaintenanceService()


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
def test_agent_config(test_session):
    """
    Create test agent configuration.

    Args:
        test_session: Test database session

    Returns:
        AgentConfiguration: Test agent configuration
    """
    config = AgentConfiguration(
        name="Test Documentation Agent",
        description="Test documentation agent configuration",
        agent_type=AgentType.DOCUMENTATION,
        model_size=ModelSize.MEDIUM,
        temperature=0.7,
        max_tokens=4000,
        system_prompt="You are a helpful documentation assistant."
    )
    test_session.add(config)
    test_session.commit()

    return config


@pytest.fixture
def test_conversation(test_session):
    """
    Create a test conversation.

    Args:
        test_session: Test database session

    Returns:
        Conversation: Test conversation
    """
    from app.models.conversation import Conversation
    
    conversation = Conversation(
        conversation_id=uuid.uuid4(),
        title="Test Conversation",
        user_id=1,
        agent_type=AgentType.DOCUMENTATION,
        is_active=True
    )
    test_session.add(conversation)
    test_session.commit()

    return conversation


@pytest.fixture
def test_messages(test_session, test_conversation):
    """
    Create test messages for a conversation.

    Args:
        test_session: Test database session
        test_conversation: Test conversation

    Returns:
        List[Message]: Test messages
    """
    messages = [
        Message(
            conversation_id=test_conversation.id,
            role=MessageRole.SYSTEM,
            content="You are a helpful documentation assistant."
        ),
        Message(
            conversation_id=test_conversation.id,
            role=MessageRole.USER,
            content="Where can I find information about landing gear maintenance?"
        ),
        Message(
            conversation_id=test_conversation.id,
            role=MessageRole.ASSISTANT,
            content="You can find information about landing gear maintenance in the Aircraft Maintenance Manual, Chapter 32."
        )
    ]
    
    for message in messages:
        test_session.add(message)
    
    test_session.commit()
    
    return messages


@pytest.fixture
def mock_documentation_agent(mock_llm_service, mock_documentation_service):
    """
    Create a mock documentation agent.

    Args:
        mock_llm_service: Mock LLM service
        mock_documentation_service: Mock documentation service

    Returns:
        MagicMock: Mock documentation agent
    """
    agent = MagicMock()
    agent.llm_service = mock_llm_service
    agent.documentation_service = mock_documentation_service
    
    # Mock process_query method
    agent.process_query = AsyncMock(return_value={
        "response": "This is a mock response from the documentation agent.",
        "sources": [
            {
                "id": "doc-001",
                "title": "Test Document 1",
                "content": "This is test content for document 1",
                "relevance": 0.9
            }
        ]
    })
    
    return agent


@pytest.fixture
def mock_troubleshooting_agent(mock_llm_service, mock_troubleshooting_service):
    """
    Create a mock troubleshooting agent.

    Args:
        mock_llm_service: Mock LLM service
        mock_troubleshooting_service: Mock troubleshooting service

    Returns:
        MagicMock: Mock troubleshooting agent
    """
    agent = MagicMock()
    agent.llm_service = mock_llm_service
    agent.troubleshooting_service = mock_troubleshooting_service
    
    # Mock process_query method
    agent.process_query = AsyncMock(return_value={
        "response": "This is a mock response from the troubleshooting agent.",
        "diagnosis": {
            "potential_causes": [
                {
                    "id": "cause-001",
                    "description": "Faulty component",
                    "probability": 0.75
                }
            ],
            "recommended_actions": [
                {
                    "id": "action-001",
                    "description": "Inspect component",
                    "priority": "high"
                }
            ]
        }
    })
    
    return agent


@pytest.fixture
def mock_maintenance_agent(mock_llm_service, mock_maintenance_service):
    """
    Create a mock maintenance agent.

    Args:
        mock_llm_service: Mock LLM service
        mock_maintenance_service: Mock maintenance service

    Returns:
        MagicMock: Mock maintenance agent
    """
    agent = MagicMock()
    agent.llm_service = mock_llm_service
    agent.maintenance_service = mock_maintenance_service
    
    # Mock process_query method
    agent.process_query = AsyncMock(return_value={
        "response": "This is a mock response from the maintenance agent.",
        "procedure": {
            "title": "Test Procedure",
            "steps": [
                {
                    "step_number": 1,
                    "description": "Prepare the work area"
                },
                {
                    "step_number": 2,
                    "description": "Perform the maintenance"
                }
            ],
            "tools_required": ["Tool 1", "Tool 2"]
        }
    })
    
    return agent
