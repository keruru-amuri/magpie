"""
Integration tests for agent components.
"""
import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch

from app.models.conversation import AgentType, Conversation, Message, MessageRole
from app.models.agent import AgentConfiguration, ModelSize
from app.core.agents.documentation_agent import DocumentationAgent
from app.core.agents.troubleshooting_agent import TroubleshootingAgent
from app.core.agents.maintenance_agent import MaintenanceAgent
from app.services.llm_service import LLMService

# Import agent fixtures
pytest_plugins = ["tests.conftest_agent"]


class TestAgentIntegration:
    """
    Integration tests for agent components.
    """
    
    @pytest.mark.asyncio
    async def test_documentation_agent_integration(self, mock_llm_service, mock_documentation_service):
        """
        Test integration of DocumentationAgent with services.
        """
        # Create agent
        agent = DocumentationAgent(
            llm_service=mock_llm_service,
            documentation_service=mock_documentation_service
        )
        
        # Process query
        result = await agent.process_query(
            query="Where can I find information about landing gear maintenance?",
            conversation_id=str(uuid.uuid4()),
            context={"aircraft_type": "Boeing 737"}
        )
        
        # Verify result
        assert "response" in result
        assert "sources" in result
        assert len(result["sources"]) > 0
        
        # Verify search_documents was called
        mock_documentation_service.search_documents.assert_called_once()
        
        # Verify generate_completion was called
        mock_llm_service.generate_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_troubleshooting_agent_integration(self, mock_llm_service, mock_troubleshooting_service):
        """
        Test integration of TroubleshootingAgent with services.
        """
        # Create agent
        agent = TroubleshootingAgent(
            llm_service=mock_llm_service,
            troubleshooting_service=mock_troubleshooting_service
        )
        
        # Process query
        result = await agent.process_query(
            query="The hydraulic system is making unusual noises and showing low pressure.",
            conversation_id=str(uuid.uuid4()),
            context={"aircraft_type": "Boeing 737"}
        )
        
        # Verify result
        assert "response" in result
        assert "diagnosis" in result
        assert "potential_causes" in result["diagnosis"]
        assert "recommended_actions" in result["diagnosis"]
        
        # Verify diagnose_issue was called
        mock_troubleshooting_service.diagnose_issue.assert_called_once()
        
        # Verify generate_completion was called
        mock_llm_service.generate_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_maintenance_agent_integration(self, mock_llm_service, mock_maintenance_service):
        """
        Test integration of MaintenanceAgent with services.
        """
        # Create agent
        agent = MaintenanceAgent(
            llm_service=mock_llm_service,
            maintenance_service=mock_maintenance_service
        )
        
        # Process query
        result = await agent.process_query(
            query="What are the steps to inspect the hydraulic pump on a Boeing 737?",
            conversation_id=str(uuid.uuid4()),
            context={"aircraft_type": "Boeing 737"}
        )
        
        # Verify result
        assert "response" in result
        assert "procedure" in result
        assert "title" in result["procedure"]
        assert "steps" in result["procedure"]
        
        # Verify generate_procedure was called
        mock_maintenance_service.generate_procedure.assert_called_once()
        
        # Verify generate_completion was called
        mock_llm_service.generate_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_agent_with_conversation_context(
        self,
        test_session,
        test_conversation,
        test_messages,
        mock_llm_service,
        mock_documentation_service
    ):
        """
        Test agent with conversation context.
        """
        # Create agent
        agent = DocumentationAgent(
            llm_service=mock_llm_service,
            documentation_service=mock_documentation_service
        )
        
        # Get conversation context
        from app.repositories.conversation import ConversationRepository
        repo = ConversationRepository(test_session)
        context_messages = repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )
        
        # Create context dict
        context = {
            "conversation_history": context_messages,
            "aircraft_type": "Boeing 737"
        }
        
        # Process query
        result = await agent.process_query(
            query="Can you provide more details about the landing gear maintenance?",
            conversation_id=str(test_conversation.conversation_id),
            context=context
        )
        
        # Verify result
        assert "response" in result
        assert "sources" in result
        assert len(result["sources"]) > 0
        
        # Verify search_documents was called
        mock_documentation_service.search_documents.assert_called_once()
        
        # Verify generate_completion was called
        mock_llm_service.generate_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_agent_with_user_preferences(
        self,
        test_session,
        test_conversation,
        mock_llm_service,
        mock_documentation_service
    ):
        """
        Test agent with user preferences.
        """
        # Add user preferences
        from app.models.context import UserPreference
        from app.repositories.context import UserPreferenceRepository
        
        pref_repo = UserPreferenceRepository(test_session)
        preferences = [
            UserPreference(
                user_id=test_conversation.user_id,
                preference_key="preferred_format",
                preference_value="detailed",
                confidence=0.9
            ),
            UserPreference(
                user_id=test_conversation.user_id,
                preference_key="aircraft_type",
                preference_value="Boeing 737",
                confidence=0.8
            )
        ]
        
        for pref in preferences:
            test_session.add(pref)
        
        test_session.commit()
        
        # Create agent
        agent = DocumentationAgent(
            llm_service=mock_llm_service,
            documentation_service=mock_documentation_service
        )
        
        # Get user preferences
        user_prefs = {}
        for pref in pref_repo.get_preferences_for_user(test_conversation.user_id):
            user_prefs[pref.preference_key] = pref.preference_value
        
        # Create context dict
        context = {
            "user_preferences": user_prefs,
            "aircraft_type": user_prefs.get("aircraft_type", "")
        }
        
        # Process query
        result = await agent.process_query(
            query="Can you provide information about landing gear maintenance?",
            conversation_id=str(test_conversation.conversation_id),
            context=context
        )
        
        # Verify result
        assert "response" in result
        assert "sources" in result
        assert len(result["sources"]) > 0
        
        # Verify search_documents was called with correct filters
        mock_documentation_service.search_documents.assert_called_once()
        call_args = mock_documentation_service.search_documents.call_args[0]
        call_kwargs = mock_documentation_service.search_documents.call_args[1]
        
        assert "filters" in call_kwargs
        assert call_kwargs["filters"]["aircraft_type"] == "Boeing 737"
    
    @pytest.mark.asyncio
    async def test_multi_agent_workflow(
        self,
        mock_llm_service,
        mock_documentation_service,
        mock_troubleshooting_service,
        mock_maintenance_service
    ):
        """
        Test a multi-agent workflow.
        """
        # Create agents
        doc_agent = DocumentationAgent(
            llm_service=mock_llm_service,
            documentation_service=mock_documentation_service
        )
        
        ts_agent = TroubleshootingAgent(
            llm_service=mock_llm_service,
            troubleshooting_service=mock_troubleshooting_service
        )
        
        maint_agent = MaintenanceAgent(
            llm_service=mock_llm_service,
            maintenance_service=mock_maintenance_service
        )
        
        # Create conversation ID
        conversation_id = str(uuid.uuid4())
        
        # Step 1: User asks about hydraulic system documentation
        doc_result = await doc_agent.process_query(
            query="Where can I find information about the hydraulic system on a Boeing 737?",
            conversation_id=conversation_id,
            context={"aircraft_type": "Boeing 737"}
        )
        
        # Verify documentation result
        assert "response" in doc_result
        assert "sources" in doc_result
        assert len(doc_result["sources"]) > 0
        
        # Step 2: User reports an issue with the hydraulic system
        ts_result = await ts_agent.process_query(
            query="The hydraulic system is making unusual noises and showing low pressure.",
            conversation_id=conversation_id,
            context={"aircraft_type": "Boeing 737"}
        )
        
        # Verify troubleshooting result
        assert "response" in ts_result
        assert "diagnosis" in ts_result
        assert "potential_causes" in ts_result["diagnosis"]
        assert "recommended_actions" in ts_result["diagnosis"]
        
        # Step 3: User asks for maintenance procedure
        maint_result = await maint_agent.process_query(
            query="What are the steps to inspect the hydraulic pump on a Boeing 737?",
            conversation_id=conversation_id,
            context={"aircraft_type": "Boeing 737"}
        )
        
        # Verify maintenance result
        assert "response" in maint_result
        assert "procedure" in maint_result
        assert "title" in maint_result["procedure"]
        assert "steps" in maint_result["procedure"]
        
        # Verify all services were called
        mock_documentation_service.search_documents.assert_called_once()
        mock_troubleshooting_service.diagnose_issue.assert_called_once()
        mock_maintenance_service.generate_procedure.assert_called_once()
