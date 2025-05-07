"""
Integration tests for agent and orchestrator components.
"""
import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch

from app.models.conversation import AgentType
from app.models.orchestrator import (
    OrchestratorRequest,
    OrchestratorResponse,
    RequestClassification,
    RoutingResult
)
from app.core.agents.factory import AgentFactory
from app.core.orchestrator.orchestrator import Orchestrator

# Import agent fixtures
pytest_plugins = ["tests.conftest_agent", "tests.conftest_orchestrator"]


class TestAgentOrchestratorIntegration:
    """
    Integration tests for agent and orchestrator components.
    """
    
    @pytest.fixture
    def agent_factory(
        self,
        mock_llm_service,
        mock_documentation_service,
        mock_troubleshooting_service,
        mock_maintenance_service
    ):
        """
        Create an agent factory.
        """
        return AgentFactory(
            llm_service=mock_llm_service,
            documentation_service=mock_documentation_service,
            troubleshooting_service=mock_troubleshooting_service,
            maintenance_service=mock_maintenance_service
        )
    
    @pytest.fixture
    def mock_orchestrator(
        self,
        mock_llm_service,
        mock_agent_repository,
        mock_conversation_repository,
        agent_factory
    ):
        """
        Create a mock orchestrator with real agent factory.
        """
        orchestrator = Orchestrator(
            llm_service=mock_llm_service,
            agent_repository=mock_agent_repository,
            conversation_repository=mock_conversation_repository
        )
        
        # Mock classifier
        orchestrator.classifier = MagicMock()
        orchestrator.classifier.classify_request = AsyncMock(return_value=RequestClassification(
            agent_type=AgentType.DOCUMENTATION,
            confidence=0.9,
            reasoning="This is a documentation query"
        ))
        
        # Mock router
        orchestrator.router = MagicMock()
        orchestrator.router.route_request = AsyncMock(return_value=RoutingResult(
            agent_type=AgentType.DOCUMENTATION,
            agent_config_id=1,
            classification=RequestClassification(
                agent_type=AgentType.DOCUMENTATION,
                confidence=0.9,
                reasoning="This is a documentation query"
            )
        ))
        
        # Mock formatter
        orchestrator.formatter = MagicMock()
        orchestrator.formatter.format_response = AsyncMock(return_value=OrchestratorResponse(
            response="This is a test response",
            agent_type=AgentType.DOCUMENTATION,
            agent_name="Documentation Assistant",
            confidence=0.9,
            conversation_id="test-conversation-id"
        ))
        
        # Set agent factory
        orchestrator.agent_factory = agent_factory
        
        # Mark as initialized
        orchestrator._registry_initialized = True
        
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_orchestrator_with_documentation_agent(
        self,
        mock_orchestrator,
        agent_factory,
        mock_documentation_service
    ):
        """
        Test orchestrator with documentation agent.
        """
        # Create request
        request = OrchestratorRequest(
            query="Where can I find information about landing gear maintenance?",
            user_id="test-user",
            conversation_id="test-conversation-id"
        )
        
        # Mock _generate_agent_response to use real agent
        async def mock_generate_agent_response(query, agent_config, context=None):
            # Create documentation agent
            agent = agent_factory.create_agent(AgentType.DOCUMENTATION)
            # Process query
            result = await agent.process_query(query, request.conversation_id, context)
            # Return response
            return result["response"]
        
        # Patch _generate_agent_response
        with patch.object(
            mock_orchestrator,
            '_generate_agent_response',
            side_effect=mock_generate_agent_response
        ):
            # Process request
            response = await mock_orchestrator.process_request(request)
            
            # Verify response
            assert isinstance(response, OrchestratorResponse)
            assert response.agent_type == AgentType.DOCUMENTATION
            assert response.conversation_id == "test-conversation-id"
            
            # Verify documentation service was called
            mock_documentation_service.search_documents.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_orchestrator_with_troubleshooting_agent(
        self,
        mock_orchestrator,
        agent_factory,
        mock_troubleshooting_service
    ):
        """
        Test orchestrator with troubleshooting agent.
        """
        # Create request
        request = OrchestratorRequest(
            query="The hydraulic system is making unusual noises and showing low pressure.",
            user_id="test-user",
            conversation_id="test-conversation-id"
        )
        
        # Mock classifier to return troubleshooting
        mock_orchestrator.classifier.classify_request.return_value = RequestClassification(
            agent_type=AgentType.TROUBLESHOOTING,
            confidence=0.9,
            reasoning="This is a troubleshooting query"
        )
        
        # Mock router to return troubleshooting
        mock_orchestrator.router.route_request.return_value = RoutingResult(
            agent_type=AgentType.TROUBLESHOOTING,
            agent_config_id=2,
            classification=RequestClassification(
                agent_type=AgentType.TROUBLESHOOTING,
                confidence=0.9,
                reasoning="This is a troubleshooting query"
            )
        )
        
        # Mock formatter to return troubleshooting response
        mock_orchestrator.formatter.format_response.return_value = OrchestratorResponse(
            response="This is a troubleshooting response",
            agent_type=AgentType.TROUBLESHOOTING,
            agent_name="Troubleshooting Advisor",
            confidence=0.9,
            conversation_id="test-conversation-id"
        )
        
        # Mock _generate_agent_response to use real agent
        async def mock_generate_agent_response(query, agent_config, context=None):
            # Create troubleshooting agent
            agent = agent_factory.create_agent(AgentType.TROUBLESHOOTING)
            # Process query
            result = await agent.process_query(query, request.conversation_id, context)
            # Return response
            return result["response"]
        
        # Patch _generate_agent_response
        with patch.object(
            mock_orchestrator,
            '_generate_agent_response',
            side_effect=mock_generate_agent_response
        ):
            # Process request
            response = await mock_orchestrator.process_request(request)
            
            # Verify response
            assert isinstance(response, OrchestratorResponse)
            assert response.agent_type == AgentType.TROUBLESHOOTING
            assert response.conversation_id == "test-conversation-id"
            
            # Verify troubleshooting service was called
            mock_troubleshooting_service.diagnose_issue.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_orchestrator_with_maintenance_agent(
        self,
        mock_orchestrator,
        agent_factory,
        mock_maintenance_service
    ):
        """
        Test orchestrator with maintenance agent.
        """
        # Create request
        request = OrchestratorRequest(
            query="What are the steps to inspect the hydraulic pump on a Boeing 737?",
            user_id="test-user",
            conversation_id="test-conversation-id"
        )
        
        # Mock classifier to return maintenance
        mock_orchestrator.classifier.classify_request.return_value = RequestClassification(
            agent_type=AgentType.MAINTENANCE,
            confidence=0.9,
            reasoning="This is a maintenance query"
        )
        
        # Mock router to return maintenance
        mock_orchestrator.router.route_request.return_value = RoutingResult(
            agent_type=AgentType.MAINTENANCE,
            agent_config_id=3,
            classification=RequestClassification(
                agent_type=AgentType.MAINTENANCE,
                confidence=0.9,
                reasoning="This is a maintenance query"
            )
        )
        
        # Mock formatter to return maintenance response
        mock_orchestrator.formatter.format_response.return_value = OrchestratorResponse(
            response="This is a maintenance response",
            agent_type=AgentType.MAINTENANCE,
            agent_name="Maintenance Procedure Generator",
            confidence=0.9,
            conversation_id="test-conversation-id"
        )
        
        # Mock _generate_agent_response to use real agent
        async def mock_generate_agent_response(query, agent_config, context=None):
            # Create maintenance agent
            agent = agent_factory.create_agent(AgentType.MAINTENANCE)
            # Process query
            result = await agent.process_query(query, request.conversation_id, context)
            # Return response
            return result["response"]
        
        # Patch _generate_agent_response
        with patch.object(
            mock_orchestrator,
            '_generate_agent_response',
            side_effect=mock_generate_agent_response
        ):
            # Process request
            response = await mock_orchestrator.process_request(request)
            
            # Verify response
            assert isinstance(response, OrchestratorResponse)
            assert response.agent_type == AgentType.MAINTENANCE
            assert response.conversation_id == "test-conversation-id"
            
            # Verify maintenance service was called
            mock_maintenance_service.generate_procedure.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_orchestrator_with_context(
        self,
        mock_orchestrator,
        agent_factory,
        mock_conversation_repository
    ):
        """
        Test orchestrator with context.
        """
        # Create request
        request = OrchestratorRequest(
            query="Can you provide more details about the landing gear maintenance?",
            user_id="test-user",
            conversation_id="test-conversation-id"
        )
        
        # Mock get_conversation_context
        mock_conversation_repository.get_conversation_context.return_value = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Where can I find information about landing gear maintenance?"},
            {"role": "assistant", "content": "You can find information in the Aircraft Maintenance Manual."}
        ]
        
        # Mock _generate_agent_response to use real agent
        async def mock_generate_agent_response(query, agent_config, context=None):
            # Create documentation agent
            agent = agent_factory.create_agent(AgentType.DOCUMENTATION)
            # Process query
            result = await agent.process_query(query, request.conversation_id, context)
            # Return response
            return result["response"]
        
        # Patch _generate_agent_response
        with patch.object(
            mock_orchestrator,
            '_generate_agent_response',
            side_effect=mock_generate_agent_response
        ):
            # Process request
            response = await mock_orchestrator.process_request(request)
            
            # Verify response
            assert isinstance(response, OrchestratorResponse)
            assert response.agent_type == AgentType.DOCUMENTATION
            assert response.conversation_id == "test-conversation-id"
            
            # Verify get_conversation_context was called
            mock_conversation_repository.get_conversation_context.assert_called_once()
