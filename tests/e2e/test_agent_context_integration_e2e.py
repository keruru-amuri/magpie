"""
End-to-end tests for the integration between agent components and context management.

These tests verify the seamless integration between agent components and the context
management system in realistic end-to-end scenarios, including:
- Conversation flow with context management
- Agent switching with context preservation
- Multi-agent collaboration with shared context
- Error handling and recovery
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
from app.core.context.preference_extraction import PreferenceManager
from app.core.context.summarization import ConversationSummarizer, SummaryManager
from app.core.context.pruning import (
    PriorityBasedPruning, RelevanceBasedPruning, TimeBasedPruning,
    HybridPruningStrategy
)
from app.core.agents.factory import AgentFactory
from app.core.agents.documentation_agent import DocumentationAgent
from app.core.agents.troubleshooting_agent import TroubleshootingAgent
from app.core.agents.maintenance_agent import MaintenanceAgent
from app.services.llm_service import LLMService
from app.core.mock.service import mock_data_service

# Import agent fixtures
pytest_plugins = ["tests.conftest_agent"]


class TestAgentContextIntegrationE2E:
    """
    End-to-end tests for the integration between agent components and context management.
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
            "title": "Test Agent Context Integration E2E",
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
    async def test_conversation_flow_with_context_management(
        self,
        conversation_repo,
        context_service,
        agent_factory,
        test_conversation
    ):
        """
        Test conversation flow with context management.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Step 1: Add system message
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Step 2: Create documentation agent
        doc_agent = agent_factory.create_agent(AgentType.DOCUMENTATION)
        assert isinstance(doc_agent, DocumentationAgent)

        # Step 3: Add user message
        user_message_1 = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="I need information about Boeing 737 hydraulic system maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Step 4: Get context messages
        context_messages_1 = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )
        assert len(context_messages_1) >= 2  # At least system and user messages

        # Step 5: Process query with documentation agent
        context_1 = {
            "conversation_history": context_messages_1,
            "aircraft_type": "Boeing 737"
        }

        result_1 = await doc_agent.process_query(
            query="Tell me about hydraulic system maintenance procedures.",
            conversation_id=str(test_conversation.conversation_id),
            context=context_1
        )

        # Step 6: Verify result
        assert result_1 is not None
        assert "response" in result_1
        assert len(result_1["response"]) > 0

        # Step 7: Add assistant message with response
        assistant_message_1 = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.ASSISTANT,
            content=result_1["response"],
            add_to_context=True,
            context_priority=ContextPriority.MEDIUM
        )

        # Step 8: Add follow-up user message
        user_message_2 = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="What are the common issues with the hydraulic pump?",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Step 9: Get updated context messages
        context_messages_2 = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )
        assert len(context_messages_2) >= 4  # System, user, assistant, user

        # Step 10: Process follow-up query
        context_2 = {
            "conversation_history": context_messages_2,
            "aircraft_type": "Boeing 737"
        }

        result_2 = await doc_agent.process_query(
            query="What are the common issues with the hydraulic pump?",
            conversation_id=str(test_conversation.conversation_id),
            context=context_2
        )

        # Step 11: Verify follow-up result
        assert result_2 is not None
        assert "response" in result_2
        assert len(result_2["response"]) > 0

        # Step 12: Add assistant message with response
        assistant_message_2 = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.ASSISTANT,
            content=result_2["response"],
            add_to_context=True,
            context_priority=ContextPriority.MEDIUM
        )

        # Step 13: Verify context window statistics
        window_repo = ContextWindowRepository(context_service.session)
        window = window_repo.get_active_window_for_conversation(test_conversation.id)

        from app.core.context.monitoring import ContextWindowMonitor
        monitor = ContextWindowMonitor(
            window_repo=window_repo,
            item_repo=ContextItemRepository(context_service.session)
        )

        stats = monitor.get_window_statistics(window.id)
        assert stats is not None
        assert stats["total_items"] == 5  # System, user, assistant, user, assistant
        assert stats["token_count"] > 0

    @pytest.mark.asyncio
    async def test_agent_switching_with_context_preservation(
        self,
        conversation_repo,
        context_service,
        agent_factory,
        test_conversation
    ):
        """
        Test agent switching with context preservation.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Step 1: Add system message
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Step 2: Create documentation agent
        doc_agent = agent_factory.create_agent(AgentType.DOCUMENTATION)
        assert isinstance(doc_agent, DocumentationAgent)

        # Step 3: Add user message for documentation
        user_message_1 = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="I need information about Boeing 737 hydraulic system maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Step 4: Get context messages
        context_messages_1 = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Step 5: Process query with documentation agent
        context_1 = {
            "conversation_history": context_messages_1,
            "aircraft_type": "Boeing 737"
        }

        result_1 = await doc_agent.process_query(
            query="Tell me about hydraulic system maintenance procedures.",
            conversation_id=str(test_conversation.conversation_id),
            context=context_1
        )

        # Step 6: Add assistant message with response
        assistant_message_1 = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.ASSISTANT,
            content=result_1["response"],
            add_to_context=True,
            context_priority=ContextPriority.MEDIUM
        )

        # Step 7: Switch to troubleshooting agent
        ts_agent = agent_factory.create_agent(AgentType.TROUBLESHOOTING)
        assert isinstance(ts_agent, TroubleshootingAgent)

        # Step 8: Update conversation agent type
        conversation_repo.update_conversation(
            conversation_id=test_conversation.conversation_id,
            data={"agent_type": AgentType.TROUBLESHOOTING}
        )

        # Step 9: Add user message for troubleshooting
        user_message_2 = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="The hydraulic system is making unusual noises and showing low pressure.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Step 10: Get updated context messages
        context_messages_2 = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )
        assert len(context_messages_2) >= 4  # System, user, assistant, user

        # Step 11: Process query with troubleshooting agent
        context_2 = {
            "conversation_history": context_messages_2,
            "aircraft_type": "Boeing 737",
            "system": "Hydraulic",
            "symptoms": ["unusual noises", "low pressure"]
        }

        result_2 = await ts_agent.process_query(
            query="The hydraulic system is making unusual noises and showing low pressure. What could be the problem?",
            conversation_id=str(test_conversation.conversation_id),
            context=context_2
        )

        # Step 12: Verify troubleshooting result
        assert result_2 is not None
        assert "response" in result_2
        assert len(result_2["response"]) > 0
        assert "diagnosis" in result_2
        assert "potential_causes" in result_2["diagnosis"]
        assert len(result_2["diagnosis"]["potential_causes"]) > 0

        # Step 13: Add assistant message with response
        assistant_message_2 = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.ASSISTANT,
            content=result_2["response"],
            add_to_context=True,
            context_priority=ContextPriority.MEDIUM
        )

        # Step 14: Switch to maintenance agent
        maint_agent = agent_factory.create_agent(AgentType.MAINTENANCE)
        assert isinstance(maint_agent, MaintenanceAgent)

        # Step 15: Update conversation agent type
        conversation_repo.update_conversation(
            conversation_id=test_conversation.conversation_id,
            data={"agent_type": AgentType.MAINTENANCE}
        )

        # Step 16: Add user message for maintenance
        user_message_3 = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="I need a procedure to replace the faulty hydraulic pump.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Step 17: Get updated context messages
        context_messages_3 = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )
        assert len(context_messages_3) >= 6  # System, user, assistant, user, assistant, user

        # Step 18: Process query with maintenance agent
        context_3 = {
            "conversation_history": context_messages_3,
            "aircraft_type": "Boeing 737",
            "system": "Hydraulic",
            "component": "Hydraulic Pump",
            "procedure_type": "Replacement"
        }

        result_3 = await maint_agent.process_query(
            query="Generate a procedure to replace the faulty hydraulic pump.",
            conversation_id=str(test_conversation.conversation_id),
            context=context_3
        )

        # Step 19: Verify maintenance result
        assert result_3 is not None
        assert "response" in result_3
        assert len(result_3["response"]) > 0
        assert "procedure" in result_3
        assert "steps" in result_3["procedure"]
        assert len(result_3["procedure"]["steps"]) > 0

    @pytest.mark.asyncio
    async def test_multi_agent_collaboration_with_shared_context(
        self,
        conversation_repo,
        context_service,
        agent_factory,
        test_conversation
    ):
        """
        Test multi-agent collaboration with shared context.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Step 1: Add system message
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Step 2: Create agents
        doc_agent = agent_factory.create_agent(AgentType.DOCUMENTATION)
        ts_agent = agent_factory.create_agent(AgentType.TROUBLESHOOTING)
        maint_agent = agent_factory.create_agent(AgentType.MAINTENANCE)

        # Step 3: Add user message
        user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="I'm hearing unusual noises from the Boeing 737 landing gear during retraction. I need to diagnose the issue and find the appropriate maintenance procedure.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Step 4: Get context messages
        context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Step 5: First, use documentation agent to get relevant information
        doc_context = {
            "conversation_history": context_messages,
            "aircraft_type": "Boeing 737",
            "system": "Landing Gear"
        }

        doc_result = await doc_agent.process_query(
            query="Find information about Boeing 737 landing gear retraction system.",
            conversation_id=str(test_conversation.conversation_id),
            context=doc_context
        )

        # Step 6: Add documentation agent response
        doc_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.ASSISTANT,
            content=f"[Documentation Agent] {doc_result['response']}",
            add_to_context=True,
            context_priority=ContextPriority.MEDIUM,
            metadata={"agent_type": "documentation"}
        )

        # Step 7: Get updated context messages
        updated_context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Step 8: Use troubleshooting agent to diagnose the issue
        ts_context = {
            "conversation_history": updated_context_messages,
            "aircraft_type": "Boeing 737",
            "system": "Landing Gear",
            "symptoms": ["unusual noises", "during retraction"]
        }

        ts_result = await ts_agent.process_query(
            query="Diagnose unusual noises from the Boeing 737 landing gear during retraction.",
            conversation_id=str(test_conversation.conversation_id),
            context=ts_context
        )

        # Step 9: Add troubleshooting agent response
        ts_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.ASSISTANT,
            content=f"[Troubleshooting Agent] {ts_result['response']}",
            add_to_context=True,
            context_priority=ContextPriority.MEDIUM,
            metadata={"agent_type": "troubleshooting"}
        )

        # Step 10: Get updated context messages
        final_context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Step 11: Use maintenance agent to generate a procedure
        maint_context = {
            "conversation_history": final_context_messages,
            "aircraft_type": "Boeing 737",
            "system": "Landing Gear",
            "diagnosis": ts_result.get("diagnosis", {}),
            "procedure_type": "Repair"
        }

        maint_result = await maint_agent.process_query(
            query="Generate a procedure to repair the landing gear issue based on the diagnosis.",
            conversation_id=str(test_conversation.conversation_id),
            context=maint_context
        )

        # Step 12: Add maintenance agent response
        maint_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.ASSISTANT,
            content=f"[Maintenance Agent] {maint_result['response']}",
            add_to_context=True,
            context_priority=ContextPriority.MEDIUM,
            metadata={"agent_type": "maintenance"}
        )

        # Step 13: Verify the full conversation context
        full_context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=8000,  # Large token limit to include all messages
            include_system_prompt=True
        )

        # Verify all agent responses are included
        agent_responses = 0
        for message in full_context_messages:
            if message["role"] == "assistant":
                if "[Documentation Agent]" in message["content"]:
                    agent_responses += 1
                elif "[Troubleshooting Agent]" in message["content"]:
                    agent_responses += 1
                elif "[Maintenance Agent]" in message["content"]:
                    agent_responses += 1

        assert agent_responses == 3, "All three agent responses should be included in the context"

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(
        self,
        conversation_repo,
        context_service,
        agent_factory,
        test_conversation
    ):
        """
        Test error handling and recovery.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Step 1: Add system message
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Step 2: Create documentation agent
        doc_agent = agent_factory.create_agent(AgentType.DOCUMENTATION)

        # Step 3: Add user message with invalid query
        user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="Tell me about the XYZ-999 aircraft.",  # Non-existent aircraft
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Step 4: Get context messages
        context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Step 5: Process query with documentation agent
        context = {
            "conversation_history": context_messages,
            "aircraft_type": "XYZ-999"  # Invalid aircraft type
        }

        # The agent should handle the invalid query gracefully
        result = await doc_agent.process_query(
            query="Tell me about the XYZ-999 aircraft.",
            conversation_id=str(test_conversation.conversation_id),
            context=context
        )

        # Step 6: Verify result contains error handling
        assert result is not None
        assert "response" in result
        assert len(result["response"]) > 0
        # The response should indicate that the aircraft type is not found or not supported

        # Step 7: Add assistant message with response
        assistant_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.ASSISTANT,
            content=result["response"],
            add_to_context=True,
            context_priority=ContextPriority.MEDIUM
        )

        # Step 8: Add follow-up user message with valid query
        follow_up_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="Let me try again. Tell me about the Boeing 737 aircraft.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Step 9: Get updated context messages
        updated_context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Step 10: Process follow-up query
        updated_context = {
            "conversation_history": updated_context_messages,
            "aircraft_type": "Boeing 737"  # Valid aircraft type
        }

        follow_up_result = await doc_agent.process_query(
            query="Tell me about the Boeing 737 aircraft.",
            conversation_id=str(test_conversation.conversation_id),
            context=updated_context
        )

        # Step 11: Verify follow-up result
        assert follow_up_result is not None
        assert "response" in follow_up_result
        assert len(follow_up_result["response"]) > 0
        assert "sources" in follow_up_result
        assert len(follow_up_result["sources"]) > 0

        # Step 12: Test with invalid conversation ID
        invalid_id = str(uuid.uuid4())

        # Try to get context for invalid conversation
        invalid_context_messages = conversation_repo.get_conversation_context(
            conversation_id=invalid_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Verify empty context is returned
        assert len(invalid_context_messages) == 0

        # Step 13: Test with invalid context window
        # Create a new window and make it inactive
        new_window = context_service.create_new_window(test_conversation.id)
        window_repo = ContextWindowRepository(context_service.session)
        window_repo.update(new_window.id, {"is_active": False})

        # Try to add item to inactive window
        item_repo = ContextItemRepository(context_service.session)
        with pytest.raises(Exception):
            # This should raise an exception because the window is inactive
            item_repo.create_item(
                window_id=new_window.id,
                item_type=ContextType.MESSAGE,
                source_id=user_message.id,
                priority=ContextPriority.MEDIUM
            )
