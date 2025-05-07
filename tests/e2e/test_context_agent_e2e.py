"""
End-to-end tests for the context management system and agent components.
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

# Import agent fixtures
pytest_plugins = ["tests.conftest_agent"]


class TestContextAgentE2E:
    """
    End-to-end tests for the context management system and agent components.
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
            "title": "Test E2E Conversation",
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
    async def test_full_conversation_workflow(
        self,
        conversation_repo,
        context_service,
        agent_factory,
        test_conversation
    ):
        """
        Test the full conversation workflow from context creation to agent response.
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
        assert system_message is not None

        # Step 2: Add user message
        user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="I need information about Boeing 737 landing gear maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )
        assert user_message is not None

        # Step 3: Get context for the conversation
        context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )
        assert len(context_messages) >= 2  # At least system and user messages

        # Step 4: Create an agent and process the query
        agent = agent_factory.create_agent(AgentType.DOCUMENTATION)

        # Create context dict
        context = {
            "conversation_history": context_messages,
            "aircraft_type": "Boeing 737"
        }

        # Process query
        result = await agent.process_query(
            query="Tell me about landing gear maintenance procedures.",
            conversation_id=str(test_conversation.conversation_id),
            context=context
        )

        # Verify result
        assert "response" in result
        assert "sources" in result
        assert len(result["sources"]) > 0

        # Step 5: Add assistant message
        assistant_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.ASSISTANT,
            content=result["response"],
            add_to_context=True,
            context_priority=ContextPriority.MEDIUM
        )
        assert assistant_message is not None

        # Step 6: Add follow-up user message
        follow_up_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="What tools do I need for this maintenance procedure?",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )
        assert follow_up_message is not None

        # Step 7: Get updated context
        updated_context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )
        assert len(updated_context_messages) >= 4  # All messages so far

        # Step 8: Process follow-up query
        updated_context = {
            "conversation_history": updated_context_messages,
            "aircraft_type": "Boeing 737"
        }

        follow_up_result = await agent.process_query(
            query="What tools do I need for this maintenance procedure?",
            conversation_id=str(test_conversation.conversation_id),
            context=updated_context
        )

        # Verify follow-up result
        assert "response" in follow_up_result
        assert "sources" in follow_up_result
        assert len(follow_up_result["sources"]) > 0

    @pytest.mark.asyncio
    async def test_context_window_management(
        self,
        conversation_repo,
        context_service,
        agent_factory,
        test_conversation
    ):
        """
        Test context window management during a long conversation.
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

        # Step 2: Add many messages to fill the context window
        for i in range(20):  # Add 20 message pairs
            # Add user message
            user_message = conversation_repo.add_message(
                conversation_id=test_conversation.conversation_id,
                role=MessageRole.USER,
                content=f"User message {i+1}: This is a test message about aircraft maintenance procedures for Boeing 737.",
                add_to_context=True,
                context_priority=ContextPriority.MEDIUM
            )

            # Add assistant message
            assistant_message = conversation_repo.add_message(
                conversation_id=test_conversation.conversation_id,
                role=MessageRole.ASSISTANT,
                content=f"Assistant message {i+1}: Here is information about aircraft maintenance procedures for Boeing 737.",
                add_to_context=True,
                context_priority=ContextPriority.MEDIUM
            )

        # Step 3: Get context window
        window_repo = ContextWindowRepository(context_service.session)
        window = window_repo.get_active_window_for_conversation(test_conversation.id)
        assert window is not None

        # Record token count
        initial_token_count = window.current_tokens

        # Step 4: Get context with a low token limit to force pruning
        context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=1000,  # Low token limit to force pruning
            include_system_prompt=True
        )

        # Verify context was pruned
        assert len(context_messages) < 41  # Less than all messages (system + 20 pairs)

        # Step 5: Verify system message is still included (critical priority)
        system_message_included = False
        for message in context_messages:
            if message["role"] == "system" and "You are a helpful assistant" in message["content"]:
                system_message_included = True
                break

        assert system_message_included, "System message should be included in pruned context"

        # Step 6: Get updated window
        window = window_repo.get_active_window_for_conversation(test_conversation.id)

        # Verify token count was reduced
        assert window.current_tokens <= 1000, "Token count should be reduced to fit within limit"

    @pytest.mark.asyncio
    async def test_context_summarization(
        self,
        conversation_repo,
        context_service,
        agent_factory,
        test_conversation
    ):
        """
        Test context summarization during a long conversation.
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

        # Step 2: Add messages about a specific topic
        topic_messages = [
            "I need information about Boeing 737 hydraulic system maintenance.",
            "What are the common issues with the hydraulic system?",
            "How often should the hydraulic fluid be replaced?",
            "What tools are needed for hydraulic system maintenance?",
            "Are there any safety precautions for working with hydraulic systems?"
        ]

        for i, content in enumerate(topic_messages):
            # Add user message
            user_message = conversation_repo.add_message(
                conversation_id=test_conversation.conversation_id,
                role=MessageRole.USER,
                content=content,
                add_to_context=True,
                context_priority=ContextPriority.HIGH
            )

            # Add assistant message
            assistant_message = conversation_repo.add_message(
                conversation_id=test_conversation.conversation_id,
                role=MessageRole.ASSISTANT,
                content=f"Response to question about hydraulic system: {i+1}",
                add_to_context=True,
                context_priority=ContextPriority.MEDIUM
            )

        # Step 3: Create a summarizer
        summarizer = ConversationSummarizer()

        # Step 4: Get all messages
        item_repo = ContextItemRepository(context_service.session)
        window_repo = ContextWindowRepository(context_service.session)
        window = window_repo.get_active_window_for_conversation(test_conversation.id)
        items = item_repo.get_items_for_window(window.id)

        messages = []
        for item in items:
            if item.item_type == ContextType.MESSAGE:
                message = conversation_repo.session.get(Message, item.source_id)
                if message:
                    messages.append(message)

        # Step 5: Identify segments for summarization
        segments = summarizer.identify_segments_for_summarization(
            messages=messages,
            segment_size=4,  # Small segment size for testing
            overlap=1
        )
        assert len(segments) > 0

        # Step 6: Summarize a segment
        segment = segments[0]
        summary_text = await summarizer.summarize_messages(
            messages=segment["messages"]
        )
        assert summary_text is not None
        assert len(summary_text) > 0

        # Step 7: Create summary in database
        summary = context_service.summarize_conversation_segment(
            conversation_id=test_conversation.id,
            start_message_id=segment["start_message_id"],
            end_message_id=segment["end_message_id"],
            summary_content=summary_text
        )
        assert summary is not None

        # Step 8: Add summary to context
        context_item = context_service.add_summary_to_context(
            summary_id=summary.id,
            conversation_id=test_conversation.id,
            priority=ContextPriority.HIGH
        )
        assert context_item is not None

        # Step 9: Get context with summary
        context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=2000,  # Limited token count to encourage summary inclusion
            include_system_prompt=True
        )

        # Verify summary is included
        summary_included = False
        for message in context_messages:
            if message["role"] == "system" and summary_text in message["content"]:
                summary_included = True
                break

        assert summary_included, "Summary should be included in context"

    @pytest.mark.asyncio
    async def test_multi_agent_conversation(
        self,
        conversation_repo,
        context_service,
        agent_factory,
        test_conversation
    ):
        """
        Test using multiple agent types with the same conversation context.
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

        # Step 2: Start with documentation agent
        doc_agent = agent_factory.create_agent(AgentType.DOCUMENTATION)

        # Add user message for documentation
        doc_user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="I need information about Boeing 737 hydraulic system maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Get context
        doc_context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Process query with documentation agent
        doc_context = {
            "conversation_history": doc_context_messages,
            "aircraft_type": "Boeing 737"
        }

        doc_result = await doc_agent.process_query(
            query="Tell me about hydraulic system maintenance procedures.",
            conversation_id=str(test_conversation.conversation_id),
            context=doc_context
        )

        # Add assistant message
        doc_assistant_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.ASSISTANT,
            content=doc_result["response"],
            add_to_context=True,
            context_priority=ContextPriority.MEDIUM
        )

        # Step 3: Switch to troubleshooting agent
        ts_agent = agent_factory.create_agent(AgentType.TROUBLESHOOTING)

        # Add user message for troubleshooting
        ts_user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="The hydraulic system is making unusual noises and showing low pressure.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Get updated context
        ts_context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Process query with troubleshooting agent
        ts_context = {
            "conversation_history": ts_context_messages,
            "aircraft_type": "Boeing 737"
        }

        ts_result = await ts_agent.process_query(
            query="What could be causing these issues with the hydraulic system?",
            conversation_id=str(test_conversation.conversation_id),
            context=ts_context
        )

        # Add assistant message
        ts_assistant_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.ASSISTANT,
            content=ts_result["response"],
            add_to_context=True,
            context_priority=ContextPriority.MEDIUM
        )

        # Step 4: Switch to maintenance agent
        maint_agent = agent_factory.create_agent(AgentType.MAINTENANCE)

        # Add user message for maintenance
        maint_user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="Can you provide a maintenance procedure to fix the hydraulic pump?",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Get updated context
        maint_context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Process query with maintenance agent
        maint_context = {
            "conversation_history": maint_context_messages,
            "aircraft_type": "Boeing 737"
        }

        maint_result = await maint_agent.process_query(
            query="What are the steps to repair or replace the hydraulic pump?",
            conversation_id=str(test_conversation.conversation_id),
            context=maint_context
        )

        # Add assistant message
        maint_assistant_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.ASSISTANT,
            content=maint_result["response"],
            add_to_context=True,
            context_priority=ContextPriority.MEDIUM
        )

        # Step 5: Verify the full conversation context
        final_context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=8000,  # Large token limit to include all messages
            include_system_prompt=True
        )

        # Verify all agent interactions are included
        assert len(final_context_messages) >= 7  # System + 3 user/assistant pairs

        # Verify context contains information from all three agents
        context_text = " ".join([msg["content"] for msg in final_context_messages])
        assert "hydraulic system maintenance" in context_text
        assert "unusual noises" in context_text
        assert "maintenance procedure" in context_text

    @pytest.mark.asyncio
    async def test_user_preference_tracking(
        self,
        conversation_repo,
        context_service,
        agent_factory,
        test_conversation
    ):
        """
        Test user preference tracking and incorporation into context.
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

        # Step 2: Add user message with preferences
        user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="I prefer detailed information when working on Boeing 737 aircraft. I'm a maintenance technician with 5 years of experience.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Wait for preference extraction to complete
        # This is necessary because preference extraction is done asynchronously
        import time
        time.sleep(1)

        # Step 3: Verify preferences were extracted
        preference_repo = UserPreferenceRepository(context_service.session)
        preferences = preference_repo.get_preferences_for_user(test_conversation.user_id)

        # Verify preferences
        assert len(preferences) > 0

        # Create preference manager
        preference_manager = PreferenceManager(context_service)

        # Get preferences as dict
        user_prefs = preference_manager.get_user_preferences(test_conversation.user_id)

        # Verify specific preferences
        assert "preferred_format" in user_prefs or "detail_level" in user_prefs
        assert "aircraft_type" in user_prefs
        assert "user_role" in user_prefs or "experience_level" in user_prefs

        # Step 4: Add preferences to context
        context_service.add_user_preferences_to_context(
            conversation_id=test_conversation.id,
            priority=ContextPriority.HIGH
        )

        # Step 5: Get context with preferences
        context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Verify preferences are included in context
        prefs_included = False
        for message in context_messages:
            if message["role"] == "system" and "User Preferences" in message["content"]:
                prefs_included = True
                break

        assert prefs_included, "User preferences should be included in context"

        # Step 6: Create an agent and process a query
        agent = agent_factory.create_agent(AgentType.DOCUMENTATION)

        # Create context dict
        context = {
            "conversation_history": context_messages,
            "aircraft_type": user_prefs.get("aircraft_type", "Boeing 737"),
            "user_preferences": user_prefs
        }

        # Process query
        result = await agent.process_query(
            query="Tell me about landing gear maintenance.",
            conversation_id=str(test_conversation.conversation_id),
            context=context
        )

        # Verify result
        assert "response" in result
        assert "sources" in result
        assert len(result["sources"]) > 0

    @pytest.mark.asyncio
    async def test_error_handling(
        self,
        conversation_repo,
        context_service,
        agent_factory
    ):
        """
        Test error handling in the context management system.
        """
        # Test with invalid conversation ID
        invalid_id = str(uuid.uuid4())

        # Try to get context for invalid conversation
        context_messages = conversation_repo.get_conversation_context(
            conversation_id=invalid_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Verify empty context is returned
        assert len(context_messages) == 0

        # Try to add message to invalid conversation
        message = conversation_repo.add_message(
            conversation_id=invalid_id,
            role=MessageRole.USER,
            content="Test message",
            add_to_context=True
        )

        # Verify message is not added
        assert message is None

        # Create an agent
        agent = agent_factory.create_agent(AgentType.DOCUMENTATION)

        # Try to process query with invalid conversation ID
        result = await agent.process_query(
            query="Test query",
            conversation_id=invalid_id,
            context={}
        )

        # Verify result still contains a response
        assert "response" in result
