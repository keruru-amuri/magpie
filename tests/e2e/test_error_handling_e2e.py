"""
End-to-end tests for error handling and edge cases.
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
from app.services.llm_service import LLMService

# Import agent fixtures
pytest_plugins = ["tests.conftest_agent"]


class TestErrorHandlingE2E:
    """
    End-to-end tests for error handling and edge cases.
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
            "title": "Test Error Handling Conversation",
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

    def test_invalid_conversation_id(self, conversation_repo):
        """
        Test handling of invalid conversation ID.
        """
        # Generate invalid UUID
        invalid_id = str(uuid.uuid4())

        # Try to get conversation by invalid ID
        conversation = conversation_repo.get_by_conversation_id(invalid_id)

        # Verify conversation is None
        assert conversation is None

        # Try to get context for invalid conversation
        context = conversation_repo.get_conversation_context(
            conversation_id=invalid_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Verify context is empty
        assert len(context) == 0

        # Try to add message to invalid conversation
        message = conversation_repo.add_message(
            conversation_id=invalid_id,
            role=MessageRole.USER,
            content="Test message",
            add_to_context=True
        )

        # Verify message is None
        assert message is None

    def test_invalid_message_id(self, conversation_repo, context_service, test_conversation):
        """
        Test handling of invalid message ID.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Generate invalid message ID
        invalid_id = 999999

        # Try to get message by invalid ID
        message = conversation_repo.session.get(Message, invalid_id)

        # Verify message is None
        assert message is None

        # Try to add message to context
        result = conversation_repo.add_message_to_context(invalid_id, ContextPriority.MEDIUM)

        # Verify result is False
        assert result is False

        # Try to summarize conversation segment with invalid message IDs
        with pytest.raises(Exception):
            context_service.summarize_conversation_segment(
                conversation_id=test_conversation.id,
                start_message_id=invalid_id,
                end_message_id=invalid_id + 1,
                summary_content="Test summary"
            )

    def test_empty_context(self, conversation_repo, test_conversation, agent_factory):
        """
        Test handling of empty context.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Create an agent
        agent = agent_factory.create_agent(AgentType.DOCUMENTATION)

        # Process query with empty context
        result = agent.process_query(
            query="Test query",
            conversation_id=str(test_conversation.conversation_id),
            context={}
        )

        # Verify result still contains a response
        assert "response" in result
        assert "sources" in result

    def test_malformed_messages(self, conversation_repo, test_conversation):
        """
        Test handling of malformed messages.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Try to add message with None content
        message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content=None,
            add_to_context=True
        )

        # Verify message is still created
        assert message is not None
        assert message.content is None

        # Try to add message with invalid role
        with pytest.raises(Exception):
            conversation_repo.add_message(
                conversation_id=test_conversation.conversation_id,
                role="INVALID_ROLE",
                content="Test message",
                add_to_context=True
            )

        # Try to add message with very long content
        long_content = "A" * 100000  # Very long content
        message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content=long_content,
            add_to_context=True
        )

        # Verify message is created
        assert message is not None
        assert len(message.content) == len(long_content)

        # Get context
        context = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,  # Limited token count
            include_system_prompt=True
        )

        # Verify context is pruned
        assert len(context) < 3  # Less than all messages

    def test_context_window_overflow(self, conversation_repo, context_service, test_conversation):
        """
        Test handling of context window overflow.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Add system message
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Add many messages to overflow the context window
        for i in range(50):  # Add 50 message pairs
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

        # Get context window
        window_repo = ContextWindowRepository(context_service.session)
        window = window_repo.get_active_window_for_conversation(test_conversation.id)

        # Verify window exists
        assert window is not None

        # Get context with a very low token limit
        context = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=500,  # Very low token limit
            include_system_prompt=True
        )

        # Verify context is pruned
        assert len(context) < 101  # Less than all messages (system + 50 pairs)

        # Verify system message is still included (critical priority)
        system_message_included = False
        for message in context:
            if message["role"] == "system" and "You are a helpful assistant" in message["content"]:
                system_message_included = True
                break

        assert system_message_included, "System message should be included in pruned context"

    @pytest.mark.asyncio
    async def test_agent_error_handling(self, agent_factory):
        """
        Test agent error handling.
        """
        # Create an agent
        agent = agent_factory.create_agent(AgentType.DOCUMENTATION)

        # Process query with invalid conversation ID
        result = await agent.process_query(
            query="Test query",
            conversation_id="invalid-id",
            context={}
        )

        # Verify result still contains a response
        assert "response" in result
        assert "sources" in result

        # Process query with None query
        result = await agent.process_query(
            query=None,
            conversation_id="test-conversation",
            context={}
        )

        # Verify result still contains a response
        assert "response" in result
        assert "sources" in result

        # Process query with invalid context
        result = await agent.process_query(
            query="Test query",
            conversation_id="test-conversation",
            context=None
        )

        # Verify result still contains a response
        assert "response" in result
        assert "sources" in result

    @pytest.mark.asyncio
    async def test_concurrent_context_operations(self, conversation_repo, test_conversation):
        """
        Test concurrent context operations.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Create tasks for concurrent operations
        async def add_message(i):
            return conversation_repo.add_message(
                conversation_id=test_conversation.conversation_id,
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                content=f"Message {i}",
                add_to_context=True
            )

        # Create 10 concurrent tasks
        tasks = [add_message(i) for i in range(10)]

        # Run tasks concurrently
        results = await asyncio.gather(*tasks)

        # Verify all messages were added
        assert all(result is not None for result in results)

        # Get context
        context = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Verify context contains all messages
        assert len(context) >= 10

    def test_context_persistence(self, conversation_repo, context_service, test_conversation):
        """
        Test context persistence across session restarts.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Add messages to the conversation
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="I need information about Boeing 737 maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )

        # Close the session
        conversation_repo.session.close()

        # Create a new session
        from app.core.db.connection import DatabaseConnectionFactory
        new_session = DatabaseConnectionFactory.get_session()

        # Create a new repository with the new session
        new_repo = ConversationRepository(new_session)

        # Get context from the new repository
        context = new_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )

        # Verify context contains the messages
        assert len(context) >= 2

        # Verify system message is included
        system_message_included = False
        for message in context:
            if message["role"] == "system" and "You are a helpful assistant" in message["content"]:
                system_message_included = True
                break

        assert system_message_included, "System message should be included in context"

        # Verify user message is included
        user_message_included = False
        for message in context:
            if message["role"] == "user" and "Boeing 737 maintenance" in message["content"]:
                user_message_included = True
                break

        assert user_message_included, "User message should be included in context"

        # Clean up
        new_session.close()
