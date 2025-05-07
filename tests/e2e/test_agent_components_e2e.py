"""
End-to-end tests for agent components.

These tests verify the functionality of the specialized agent components
in a realistic end-to-end scenario, including:
- DocumentationAgent functionality
- TroubleshootingAgent functionality
- MaintenanceAgent functionality
"""
import pytest
import uuid
import asyncio
from typing import Dict, List, Optional, Any

from app.models.conversation import Conversation, Message, MessageRole, AgentType
from app.models.context import (
    ContextWindow, ContextItem, ContextType, ContextPriority,
    ContextTag, ContextSummary, UserPreference
)
from app.repositories.conversation import ConversationRepository
from app.repositories.context import (
    ContextWindowRepository, ContextItemRepository,
    ContextTagRepository, ContextSummaryRepository,
    UserPreferenceRepository
)
from app.services.context_service import ContextService
from app.core.agents.factory import AgentFactory
from app.core.agents.documentation_agent import DocumentationAgent
from app.core.agents.troubleshooting_agent import TroubleshootingAgent
from app.core.agents.maintenance_agent import MaintenanceAgent
from app.services.llm_service import LLMService
from app.core.mock.service import mock_data_service

# Import agent fixtures
pytest_plugins = ["tests.conftest_agent"]


class TestAgentComponentsE2E:
    """
    End-to-end tests for agent components.
    """

    @pytest.fixture
    def db_session(self):
        """
        Create a database session.
        """
        from app.core.db.connection import DatabaseConnectionFactory
        session = DatabaseConnectionFactory.get_session()
        yield session
        session.close()

    @pytest.fixture
    def conversation_repo(self, db_session):
        """
        Create a conversation repository.
        """
        return ConversationRepository(db_session)

    @pytest.fixture
    def context_service(self, db_session):
        """
        Create a context service.
        """
        return ContextService(db_session)

    @pytest.fixture
    def llm_service(self):
        """
        Create an LLM service.
        """
        return LLMService()

    @pytest.fixture
    def agent_factory(self, llm_service):
        """
        Create an agent factory.
        """
        return AgentFactory(llm_service=llm_service)

    @pytest.fixture
    def test_user_id(self):
        """
        Create a test user ID.
        """
        return 1  # Assuming user ID 1 exists in the test database

    @pytest.fixture
    def test_conversation(self, conversation_repo, test_user_id):
        """
        Create a test conversation.
        """
        # Create conversation data
        conversation_data = {
            "user_id": test_user_id,
            "title": "Test Agent Components E2E",
            "agent_type": AgentType.DOCUMENTATION
        }

        try:
            # Create conversation
            conversation = conversation_repo.create(conversation_data)

            # Return conversation
            yield conversation

            # Clean up
            if conversation:
                try:
                    conversation_repo.delete_conversation(conversation.conversation_id)
                except Exception as e:
                    print(f"Error deleting conversation: {e}")
        except Exception as e:
            print(f"Error creating conversation: {e}")
            pytest.skip(f"Skipping test due to database setup issue: {e}")

    @pytest.mark.asyncio
    async def test_documentation_agent_search(
        self,
        conversation_repo,
        context_service,
        agent_factory,
        test_conversation
    ):
        """
        Test documentation agent search functionality.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Step 1: Add system message
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft maintenance documentation.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Step 2: Add user message
        user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="I need information about Boeing 737 hydraulic system maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Step 3: Get context messages
        context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )
        assert len(context_messages) >= 2  # At least system and user messages

        # Step 4: Create documentation agent
        agent = agent_factory.create_agent(AgentType.DOCUMENTATION)
        assert isinstance(agent, DocumentationAgent)

        # Step 5: Process query
        context = {
            "conversation_history": context_messages,
            "aircraft_type": "Boeing 737"
        }

        result = await agent.process_query(
            query="Tell me about hydraulic system maintenance procedures.",
            conversation_id=str(test_conversation.conversation_id),
            context=context
        )

        # Step 6: Verify result
        assert result is not None
        assert "response" in result
        assert len(result["response"]) > 0
        assert "sources" in result
        assert len(result["sources"]) > 0

        # Step 7: Add assistant message with response
        assistant_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.ASSISTANT,
            content=result["response"],
            add_to_context=True,
            context_priority=ContextPriority.MEDIUM
        )

        # Step 8: Process follow-up query
        follow_up_context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        follow_up_context = {
            "conversation_history": follow_up_context_messages,
            "aircraft_type": "Boeing 737"
        }

        follow_up_result = await agent.process_query(
            query="What tools do I need for hydraulic pump maintenance?",
            conversation_id=str(test_conversation.conversation_id),
            context=follow_up_context
        )

        # Step 9: Verify follow-up result
        assert follow_up_result is not None
        assert "response" in follow_up_result
        assert len(follow_up_result["response"]) > 0
        assert "sources" in follow_up_result
        assert len(follow_up_result["sources"]) > 0

    @pytest.mark.asyncio
    async def test_documentation_agent_summarization(
        self,
        conversation_repo,
        context_service,
        agent_factory,
        test_conversation
    ):
        """
        Test documentation agent summarization functionality.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Step 1: Add system message
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft maintenance documentation.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Step 2: Add user message
        user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="Can you summarize the maintenance requirements for the Boeing 737 landing gear?",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Step 3: Get context messages
        context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Step 4: Create documentation agent
        agent = agent_factory.create_agent(AgentType.DOCUMENTATION)
        assert isinstance(agent, DocumentationAgent)

        # Step 5: Process query
        context = {
            "conversation_history": context_messages,
            "aircraft_type": "Boeing 737",
            "summarize": True
        }

        result = await agent.process_query(
            query="Summarize the maintenance requirements for the Boeing 737 landing gear.",
            conversation_id=str(test_conversation.conversation_id),
            context=context
        )

        # Step 6: Verify result
        assert result is not None
        assert "response" in result
        assert len(result["response"]) > 0
        assert "sources" in result
        assert len(result["sources"]) > 0
        assert "summary" in result
        assert len(result["summary"]) > 0

    @pytest.mark.asyncio
    async def test_documentation_agent_cross_referencing(
        self,
        conversation_repo,
        context_service,
        agent_factory,
        test_conversation
    ):
        """
        Test documentation agent cross-referencing functionality.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Step 1: Add system message
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft maintenance documentation.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Step 2: Add user message
        user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="Compare the maintenance procedures for hydraulic pumps in the Boeing 737 and Airbus A320.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Step 3: Get context messages
        context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Step 4: Create documentation agent
        agent = agent_factory.create_agent(AgentType.DOCUMENTATION)
        assert isinstance(agent, DocumentationAgent)

        # Step 5: Process query
        context = {
            "conversation_history": context_messages,
            "aircraft_types": ["Boeing 737", "Airbus A320"],
            "compare_documents": True
        }

        result = await agent.process_query(
            query="Compare the maintenance procedures for hydraulic pumps in the Boeing 737 and Airbus A320.",
            conversation_id=str(test_conversation.conversation_id),
            context=context
        )

        # Step 6: Verify result
        assert result is not None
        assert "response" in result
        assert len(result["response"]) > 0
        assert "sources" in result
        assert len(result["sources"]) > 0
        assert "comparison" in result
        assert "similarities" in result["comparison"]
        assert "differences" in result["comparison"]

    @pytest.mark.asyncio
    async def test_troubleshooting_agent_symptom_analysis(
        self,
        conversation_repo,
        context_service,
        agent_factory,
        test_conversation
    ):
        """
        Test troubleshooting agent symptom analysis functionality.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Step 1: Update conversation agent type
        conversation_repo.update_conversation(
            conversation_id=test_conversation.conversation_id,
            data={"agent_type": AgentType.TROUBLESHOOTING}
        )

        # Step 2: Add system message
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft troubleshooting.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Step 3: Add user message
        user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="The Boeing 737 hydraulic system is making unusual noises and showing low pressure.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Step 4: Get context messages
        context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Step 5: Create troubleshooting agent
        agent = agent_factory.create_agent(AgentType.TROUBLESHOOTING)
        assert isinstance(agent, TroubleshootingAgent)

        # Step 6: Process query
        context = {
            "conversation_history": context_messages,
            "aircraft_type": "Boeing 737",
            "system": "Hydraulic",
            "symptoms": ["unusual noises", "low pressure"]
        }

        result = await agent.process_query(
            query="The hydraulic system is making unusual noises and showing low pressure. What could be the problem?",
            conversation_id=str(test_conversation.conversation_id),
            context=context
        )

        # Step 7: Verify result
        assert result is not None
        assert "response" in result
        assert len(result["response"]) > 0
        assert "diagnosis" in result
        assert "potential_causes" in result["diagnosis"]
        assert len(result["diagnosis"]["potential_causes"]) > 0

    @pytest.mark.asyncio
    async def test_troubleshooting_agent_diagnostic_decision_tree(
        self,
        conversation_repo,
        context_service,
        agent_factory,
        test_conversation
    ):
        """
        Test troubleshooting agent diagnostic decision tree functionality.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Step 1: Update conversation agent type
        conversation_repo.update_conversation(
            conversation_id=test_conversation.conversation_id,
            data={"agent_type": AgentType.TROUBLESHOOTING}
        )

        # Step 2: Add system message
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft troubleshooting.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Step 3: Add user message
        user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="The Boeing 737 landing gear won't fully retract after takeoff.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Step 4: Get context messages
        context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Step 5: Create troubleshooting agent
        agent = agent_factory.create_agent(AgentType.TROUBLESHOOTING)
        assert isinstance(agent, TroubleshootingAgent)

        # Step 6: Process query
        context = {
            "conversation_history": context_messages,
            "aircraft_type": "Boeing 737",
            "system": "Landing Gear",
            "symptoms": ["won't fully retract"]
        }

        result = await agent.process_query(
            query="The landing gear won't fully retract after takeoff. What should I check?",
            conversation_id=str(test_conversation.conversation_id),
            context=context
        )

        # Step 7: Verify result
        assert result is not None
        assert "response" in result
        assert len(result["response"]) > 0
        assert "diagnosis" in result
        assert "troubleshooting_steps" in result["diagnosis"]
        assert len(result["diagnosis"]["troubleshooting_steps"]) > 0

        # Step 8: Add assistant message with response
        assistant_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.ASSISTANT,
            content=result["response"],
            add_to_context=True,
            context_priority=ContextPriority.MEDIUM
        )

        # Step 9: Add follow-up user message
        follow_up_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="I checked the hydraulic pressure and it's normal, but there's a mechanical binding in the gear mechanism.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Step 10: Get updated context messages
        updated_context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Step 11: Process follow-up query
        updated_context = {
            "conversation_history": updated_context_messages,
            "aircraft_type": "Boeing 737",
            "system": "Landing Gear",
            "symptoms": ["won't fully retract", "mechanical binding"],
            "checked": ["hydraulic pressure"]
        }

        follow_up_result = await agent.process_query(
            query="I checked the hydraulic pressure and it's normal, but there's a mechanical binding in the gear mechanism. What should I do next?",
            conversation_id=str(test_conversation.conversation_id),
            context=updated_context
        )

        # Step 12: Verify follow-up result
        assert follow_up_result is not None
        assert "response" in follow_up_result
        assert len(follow_up_result["response"]) > 0
        assert "diagnosis" in follow_up_result
        assert "updated_troubleshooting_steps" in follow_up_result["diagnosis"]
        assert len(follow_up_result["diagnosis"]["updated_troubleshooting_steps"]) > 0

    @pytest.mark.asyncio
    async def test_maintenance_agent_procedure_generation(
        self,
        conversation_repo,
        context_service,
        agent_factory,
        test_conversation
    ):
        """
        Test maintenance agent procedure generation functionality.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Step 1: Update conversation agent type
        conversation_repo.update_conversation(
            conversation_id=test_conversation.conversation_id,
            data={"agent_type": AgentType.MAINTENANCE}
        )

        # Step 2: Add system message
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft maintenance procedures.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Step 3: Add user message
        user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="I need a procedure for replacing the hydraulic pump on a Boeing 737.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Step 4: Get context messages
        context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Step 5: Create maintenance agent
        agent = agent_factory.create_agent(AgentType.MAINTENANCE)
        assert isinstance(agent, MaintenanceAgent)

        # Step 6: Process query
        context = {
            "conversation_history": context_messages,
            "aircraft_type": "Boeing 737",
            "system": "Hydraulic",
            "component": "Hydraulic Pump",
            "procedure_type": "Replacement"
        }

        result = await agent.process_query(
            query="Generate a procedure for replacing the hydraulic pump on a Boeing 737.",
            conversation_id=str(test_conversation.conversation_id),
            context=context
        )

        # Step 7: Verify result
        assert result is not None
        assert "response" in result
        assert len(result["response"]) > 0
        assert "procedure" in result
        assert "title" in result["procedure"]
        assert "steps" in result["procedure"]
        assert len(result["procedure"]["steps"]) > 0
        assert "tools_required" in result["procedure"]
        assert len(result["procedure"]["tools_required"]) > 0
        assert "safety_precautions" in result["procedure"]
        assert len(result["procedure"]["safety_precautions"]) > 0

    @pytest.mark.asyncio
    async def test_maintenance_agent_regulatory_integration(
        self,
        conversation_repo,
        context_service,
        agent_factory,
        test_conversation
    ):
        """
        Test maintenance agent regulatory requirement integration.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Step 1: Update conversation agent type
        conversation_repo.update_conversation(
            conversation_id=test_conversation.conversation_id,
            data={"agent_type": AgentType.MAINTENANCE}
        )

        # Step 2: Add system message
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft maintenance procedures.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Step 3: Add user message
        user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="I need a procedure for fuel tank inspection on a Boeing 737 that complies with FAA regulations.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Step 4: Get context messages
        context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Step 5: Create maintenance agent
        agent = agent_factory.create_agent(AgentType.MAINTENANCE)
        assert isinstance(agent, MaintenanceAgent)

        # Step 6: Process query
        context = {
            "conversation_history": context_messages,
            "aircraft_type": "Boeing 737",
            "system": "Fuel",
            "component": "Fuel Tank",
            "procedure_type": "Inspection",
            "regulatory_authority": "FAA"
        }

        result = await agent.process_query(
            query="Generate a procedure for fuel tank inspection on a Boeing 737 that complies with FAA regulations.",
            conversation_id=str(test_conversation.conversation_id),
            context=context
        )

        # Step 7: Verify result
        assert result is not None
        assert "response" in result
        assert len(result["response"]) > 0
        assert "procedure" in result
        assert "title" in result["procedure"]
        assert "steps" in result["procedure"]
        assert len(result["procedure"]["steps"]) > 0
        assert "regulatory_references" in result["procedure"]
        assert len(result["procedure"]["regulatory_references"]) > 0
        assert "compliance_notes" in result["procedure"]
        assert len(result["procedure"]["compliance_notes"]) > 0

    @pytest.mark.asyncio
    async def test_maintenance_agent_aircraft_configuration(
        self,
        conversation_repo,
        context_service,
        agent_factory,
        test_conversation
    ):
        """
        Test maintenance agent aircraft configuration customization.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Step 1: Update conversation agent type
        conversation_repo.update_conversation(
            conversation_id=test_conversation.conversation_id,
            data={"agent_type": AgentType.MAINTENANCE}
        )

        # Step 2: Add system message
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft maintenance procedures.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Step 3: Add user message
        user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="I need a procedure for APU maintenance on a Boeing 737-800 with the enhanced APU modification.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Step 4: Get context messages
        context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Step 5: Create maintenance agent
        agent = agent_factory.create_agent(AgentType.MAINTENANCE)
        assert isinstance(agent, MaintenanceAgent)

        # Step 6: Process query
        context = {
            "conversation_history": context_messages,
            "aircraft_type": "Boeing 737-800",
            "system": "APU",
            "procedure_type": "Maintenance",
            "configuration": {
                "model_variant": "737-800",
                "modifications": ["Enhanced APU"]
            }
        }

        result = await agent.process_query(
            query="Generate a procedure for APU maintenance on a Boeing 737-800 with the enhanced APU modification.",
            conversation_id=str(test_conversation.conversation_id),
            context=context
        )

        # Step 7: Verify result
        assert result is not None
        assert "response" in result
        assert len(result["response"]) > 0
        assert "procedure" in result
        assert "title" in result["procedure"]
        assert "steps" in result["procedure"]
        assert len(result["procedure"]["steps"]) > 0
        assert "configuration_notes" in result["procedure"]
        assert "enhanced APU" in result["procedure"]["configuration_notes"].lower()
