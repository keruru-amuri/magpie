"""
Unit tests for the main orchestrator.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.orchestrator.classifier import RequestClassifier
from app.core.orchestrator.formatter import ResponseFormatter
from app.core.orchestrator.orchestrator import Orchestrator
from app.core.orchestrator.registry import AgentRegistry
from app.core.orchestrator.router import Router
from app.models.conversation import AgentType
from app.models.orchestrator import (
    OrchestratorRequest,
    OrchestratorResponse,
    RequestClassification,
    RoutingResult,
)


@pytest.fixture
def mock_llm_service():
    """
    Create a mock LLM service.
    """
    mock_service = AsyncMock()
    mock_service.generate_custom_response_async = AsyncMock(return_value={"content": "Test response"})
    return mock_service


@pytest.fixture
def mock_agent_repository():
    """
    Create a mock agent repository.
    """
    mock_repo = MagicMock()
    
    # Mock agent configuration
    mock_config = MagicMock()
    mock_config.id = 1
    mock_config.agent_type = AgentType.DOCUMENTATION
    mock_config.name = "Documentation Assistant"
    mock_config.system_prompt = "You are a helpful documentation assistant."
    mock_config.model_size = "medium"
    mock_config.temperature = 0.7
    mock_config.max_tokens = 4000
    
    mock_repo.get_by_id.return_value = mock_config
    
    return mock_repo


@pytest.fixture
def mock_conversation_repository():
    """
    Create a mock conversation repository.
    """
    mock_repo = MagicMock()
    mock_repo.get_messages = MagicMock(return_value=[])
    mock_repo.add_message = MagicMock()
    return mock_repo


@pytest.fixture
def mock_classifier():
    """
    Create a mock request classifier.
    """
    mock_classifier = AsyncMock(spec=RequestClassifier)
    mock_classifier.classify_request = AsyncMock(
        return_value=RequestClassification(
            agent_type=AgentType.DOCUMENTATION,
            confidence=0.9,
            reasoning="This is a documentation request"
        )
    )
    return mock_classifier


@pytest.fixture
def mock_router():
    """
    Create a mock router.
    """
    mock_router = AsyncMock(spec=Router)
    mock_router.route_request = AsyncMock(
        return_value=RoutingResult(
            agent_type=AgentType.DOCUMENTATION,
            agent_config_id=1,
            classification=RequestClassification(
                agent_type=AgentType.DOCUMENTATION,
                confidence=0.9,
                reasoning="This is a documentation request"
            ),
            requires_followup=False,
            requires_multiple_agents=False
        )
    )
    return mock_router


@pytest.fixture
def mock_formatter():
    """
    Create a mock response formatter.
    """
    mock_formatter = MagicMock(spec=ResponseFormatter)
    mock_formatter.format_response = MagicMock(
        return_value=OrchestratorResponse(
            response="Test response",
            agent_type=AgentType.DOCUMENTATION,
            agent_name="Documentation Assistant",
            confidence=0.9,
            conversation_id="test-conversation-id"
        )
    )
    return mock_formatter


@pytest.fixture
def orchestrator(
    mock_llm_service,
    mock_agent_repository,
    mock_conversation_repository,
    mock_classifier,
    mock_router,
    mock_formatter
):
    """
    Create an orchestrator with mock components.
    """
    orchestrator = Orchestrator(
        llm_service=mock_llm_service,
        agent_repository=mock_agent_repository,
        conversation_repository=mock_conversation_repository
    )
    
    # Replace components with mocks
    orchestrator.classifier = mock_classifier
    orchestrator.router = mock_router
    orchestrator.formatter = mock_formatter
    
    # Mark as initialized
    orchestrator._registry_initialized = True
    
    return orchestrator


class TestOrchestrator:
    """
    Tests for the Orchestrator class.
    """

    @pytest.mark.asyncio
    async def test_process_request_basic(self, orchestrator, mock_classifier, mock_router, mock_formatter):
        """
        Test processing a basic request.
        """
        # Create request
        request = OrchestratorRequest(
            query="Where can I find information about landing gear maintenance?",
            user_id="test-user",
            conversation_id="test-conversation-id"
        )
        
        # Process request
        result = await orchestrator.process_request(request)
        
        # Verify result
        assert isinstance(result, OrchestratorResponse)
        assert result.response == "Test response"
        assert result.agent_type == AgentType.DOCUMENTATION
        assert result.agent_name == "Documentation Assistant"
        assert result.confidence == 0.9
        assert result.conversation_id == "test-conversation-id"
        
        # Verify components were called correctly
        mock_classifier.classify_request.assert_called_once()
        mock_router.route_request.assert_called_once()
        mock_formatter.format_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_request_with_context(self, orchestrator, mock_classifier, mock_router, mock_formatter, mock_llm_service):
        """
        Test processing a request with additional context.
        """
        # Create request with context
        request = OrchestratorRequest(
            query="Where can I find information about landing gear maintenance?",
            user_id="test-user",
            conversation_id="test-conversation-id",
            context={"aircraft_type": "Boeing 737", "manual_section": "Landing Gear"}
        )
        
        # Process request
        result = await orchestrator.process_request(request)
        
        # Verify result
        assert isinstance(result, OrchestratorResponse)
        
        # Verify LLM service was called with context
        mock_llm_service.generate_custom_response_async.assert_called_once()
        call_args = mock_llm_service.generate_custom_response_async.call_args[1]
        assert any("Boeing 737" in msg.get("content", "") for msg in call_args["messages"] if isinstance(msg, dict))

    @pytest.mark.asyncio
    async def test_process_request_without_conversation_id(self, orchestrator, mock_formatter):
        """
        Test processing a request without a conversation ID.
        """
        # Create request without conversation ID
        request = OrchestratorRequest(
            query="Where can I find information about landing gear maintenance?",
            user_id="test-user"
        )
        
        # Process request
        result = await orchestrator.process_request(request)
        
        # Verify result
        assert isinstance(result, OrchestratorResponse)
        assert result.conversation_id is not None  # Should generate a UUID
        
        # Verify formatter was called with a generated conversation ID
        mock_formatter.format_response.assert_called_once()
        call_args = mock_formatter.format_response.call_args[1]
        assert "conversation_id" in call_args
        assert call_args["conversation_id"] is not None

    @pytest.mark.asyncio
    async def test_process_request_error_handling(self, orchestrator, mock_classifier):
        """
        Test error handling during request processing.
        """
        # Configure classifier to raise an exception
        mock_classifier.classify_request.side_effect = Exception("Test error")
        
        # Create request
        request = OrchestratorRequest(
            query="Where can I find information about landing gear maintenance?",
            user_id="test-user",
            conversation_id="test-conversation-id"
        )
        
        # Process request (should not raise an exception)
        result = await orchestrator.process_request(request)
        
        # Verify result contains an error message
        assert isinstance(result, OrchestratorResponse)
        assert "error" in result.response.lower() or "apologize" in result.response.lower()
        assert result.agent_type == AgentType.DOCUMENTATION
        assert result.confidence == 0.0
        assert result.metadata is not None
        assert "error" in result.metadata

    @pytest.mark.asyncio
    async def test_initialize(self, mock_llm_service, mock_agent_repository, mock_conversation_repository):
        """
        Test initializing the orchestrator.
        """
        # Create orchestrator without mocked components
        orchestrator = Orchestrator(
            llm_service=mock_llm_service,
            agent_repository=mock_agent_repository,
            conversation_repository=mock_conversation_repository
        )
        
        # Mock agent registry initialize method
        orchestrator.agent_registry.initialize = AsyncMock()
        
        # Initialize orchestrator
        await orchestrator.initialize()
        
        # Verify agent registry was initialized
        orchestrator.agent_registry.initialize.assert_called_once()
        assert orchestrator._registry_initialized is True
        
        # Initialize again (should not call initialize again)
        orchestrator.agent_registry.initialize.reset_mock()
        await orchestrator.initialize()
        orchestrator.agent_registry.initialize.assert_not_called()

    def test_get_default_system_prompt(self, orchestrator):
        """
        Test getting default system prompts for different agent types.
        """
        # Test documentation agent
        prompt = orchestrator._get_default_system_prompt(AgentType.DOCUMENTATION)
        assert "documentation" in prompt.lower()
        
        # Test troubleshooting agent
        prompt = orchestrator._get_default_system_prompt(AgentType.TROUBLESHOOTING)
        assert "troubleshoot" in prompt.lower()
        
        # Test maintenance agent
        prompt = orchestrator._get_default_system_prompt(AgentType.MAINTENANCE)
        assert "maintenance" in prompt.lower()
        
        # Test unknown agent type
        prompt = orchestrator._get_default_system_prompt("unknown")
        assert "assistant" in prompt.lower()

    @pytest.mark.asyncio
    async def test_generate_agent_response(self, orchestrator, mock_llm_service):
        """
        Test generating an agent response.
        """
        # Mock agent config
        agent_config = MagicMock()
        agent_config.agent_type = AgentType.DOCUMENTATION
        agent_config.system_prompt = "You are a helpful documentation assistant."
        agent_config.model_size = "medium"
        agent_config.temperature = 0.7
        agent_config.max_tokens = 4000
        
        # Generate response
        response = await orchestrator._generate_agent_response(
            query="Where can I find information about landing gear maintenance?",
            agent_config=agent_config,
            context={"aircraft_type": "Boeing 737"}
        )
        
        # Verify result
        assert response == "Test response"
        
        # Verify LLM service was called correctly
        mock_llm_service.generate_custom_response_async.assert_called_once()
        call_args = mock_llm_service.generate_custom_response_async.call_args[1]
        assert call_args["model_size"] == "medium"
        assert call_args["temperature"] == 0.7
        assert call_args["max_tokens"] == 4000
        assert len(call_args["messages"]) == 2  # System prompt + user query

    @pytest.mark.asyncio
    async def test_generate_agent_response_with_conversation_history(self, orchestrator, mock_llm_service):
        """
        Test generating an agent response with conversation history.
        """
        # Mock agent config
        agent_config = MagicMock()
        agent_config.agent_type = AgentType.DOCUMENTATION
        agent_config.system_prompt = "You are a helpful documentation assistant."
        agent_config.model_size = "medium"
        agent_config.temperature = 0.7
        agent_config.max_tokens = 4000
        
        # Mock conversation history
        conversation_history = [
            {"role": "user", "content": "I need information about landing gear maintenance."},
            {"role": "assistant", "content": "I can help you find information about landing gear maintenance."}
        ]
        
        # Generate response
        response = await orchestrator._generate_agent_response(
            query="Where can I find that information?",
            agent_config=agent_config,
            conversation_history=conversation_history
        )
        
        # Verify result
        assert response == "Test response"
        
        # Verify LLM service was called correctly
        mock_llm_service.generate_custom_response_async.assert_called_once()
        call_args = mock_llm_service.generate_custom_response_async.call_args[1]
        assert len(call_args["messages"]) == 4  # System prompt + 2 history messages + user query
