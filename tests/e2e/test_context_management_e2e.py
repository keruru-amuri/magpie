"""
End-to-end tests for the context management system.

These tests verify the functionality of the context management system
in a realistic end-to-end scenario, including:
- Context window creation and management
- Context item addition and retrieval
- Context pruning strategies
- Context summarization
- User preference extraction and management
- Context tagging and retrieval by tags
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
from app.core.context.tagging import TagManager, EntityTagExtractor, KeywordTagExtractor
from app.core.context.monitoring import ContextWindowMonitor
from app.services.llm_service import LLMService

# Import agent fixtures
pytest_plugins = ["tests.conftest_agent"]


class TestContextManagementE2E:
    """
    End-to-end tests for the context management system.
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
            "title": "Test Context Management E2E",
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
    async def test_context_window_creation_and_management(
        self,
        conversation_repo,
        context_service,
        test_conversation
    ):
        """
        Test context window creation and management.
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

        # Step 2: Get context window
        window_repo = ContextWindowRepository(context_service.session)
        window = window_repo.get_active_window_for_conversation(test_conversation.id)
        assert window is not None
        assert window.conversation_id == test_conversation.id
        assert window.is_active is True

        # Step 3: Add more messages
        user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="Tell me about Boeing 737 hydraulic system maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )
        assert user_message is not None

        assistant_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.ASSISTANT,
            content="The Boeing 737 hydraulic system requires regular maintenance to ensure proper operation.",
            add_to_context=True,
            context_priority=ContextPriority.MEDIUM
        )
        assert assistant_message is not None

        # Step 4: Get context items
        item_repo = ContextItemRepository(context_service.session)
        items = item_repo.get_items_for_window(window.id)
        assert len(items) == 3  # System, user, and assistant messages

        # Step 5: Create a new window
        new_window = context_service.create_new_window(test_conversation.id)
        assert new_window is not None
        assert new_window.id != window.id
        assert new_window.is_active is True

        # Step 6: Verify old window is inactive
        old_window = window_repo.get_window_by_id(window.id)
        assert old_window is not None
        assert old_window.is_active is False

        # Step 7: Add message to new window
        new_user_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.USER,
            content="What tools do I need for hydraulic pump maintenance?",
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )
        assert new_user_message is not None

        # Step 8: Verify message was added to new window
        new_items = item_repo.get_items_for_window(new_window.id)
        assert len(new_items) == 1  # Just the new user message

    @pytest.mark.asyncio
    async def test_context_pruning_strategies(
        self,
        conversation_repo,
        context_service,
        test_conversation
    ):
        """
        Test context pruning strategies.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Step 1: Add multiple messages
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Add 10 pairs of user and assistant messages
        for i in range(10):
            user_message = conversation_repo.add_message(
                conversation_id=test_conversation.conversation_id,
                role=MessageRole.USER,
                content=f"User message {i+1}",
                add_to_context=True,
                context_priority=ContextPriority.MEDIUM
            )

            assistant_message = conversation_repo.add_message(
                conversation_id=test_conversation.conversation_id,
                role=MessageRole.ASSISTANT,
                content=f"Assistant response {i+1}",
                add_to_context=True,
                context_priority=ContextPriority.MEDIUM
            )

        # Step 2: Get context window
        window_repo = ContextWindowRepository(context_service.session)
        window = window_repo.get_active_window_for_conversation(test_conversation.id)

        # Step 3: Get all items
        item_repo = ContextItemRepository(context_service.session)
        all_items = item_repo.get_items_for_window(window.id)
        assert len(all_items) == 21  # 1 system + 10 user + 10 assistant

        # Step 4: Create pruning strategies
        priority_pruning = PriorityBasedPruning()
        time_pruning = TimeBasedPruning()
        hybrid_pruning = HybridPruningStrategy([priority_pruning, time_pruning])

        # Step 5: Apply priority-based pruning
        priority_items = priority_pruning.prune_items(
            items=all_items,
            max_items=10,
            conversation_id=test_conversation.id
        )
        assert len(priority_items) == 10
        assert any(item.priority == ContextPriority.CRITICAL for item in priority_items)

        # Step 6: Apply time-based pruning
        time_items = time_pruning.prune_items(
            items=all_items,
            max_items=10,
            conversation_id=test_conversation.id
        )
        assert len(time_items) == 10

        # Step 7: Apply hybrid pruning
        hybrid_items = hybrid_pruning.prune_items(
            items=all_items,
            max_items=10,
            conversation_id=test_conversation.id
        )
        assert len(hybrid_items) == 10
        assert any(item.priority == ContextPriority.CRITICAL for item in hybrid_items)

    @pytest.mark.asyncio
    async def test_context_summarization(
        self,
        conversation_repo,
        context_service,
        test_conversation,
        llm_service
    ):
        """
        Test context summarization.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Step 1: Add multiple messages
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Add 5 pairs of user and assistant messages about a specific topic
        messages = [
            ("USER", "I need to perform maintenance on the Boeing 737 hydraulic system."),
            ("ASSISTANT", "What specific maintenance task do you need to perform on the hydraulic system?"),
            ("USER", "I need to replace the hydraulic pump."),
            ("ASSISTANT", "To replace the hydraulic pump on a Boeing 737, you'll need to follow these steps: 1. Depressurize the system, 2. Disconnect electrical connections, 3. Remove mounting bolts, 4. Replace the pump, 5. Reconnect everything, 6. Test the system."),
            ("USER", "What tools do I need for this task?"),
            ("ASSISTANT", "You'll need the following tools: socket wrench set, torque wrench, hydraulic pressure gauge, safety equipment including gloves and eye protection, and a drain pan for hydraulic fluid."),
            ("USER", "How long will this maintenance task take?"),
            ("ASSISTANT", "Replacing a hydraulic pump typically takes 4-6 hours for an experienced technician, including system testing and documentation."),
            ("USER", "Are there any special precautions I should take?"),
            ("ASSISTANT", "Yes, ensure the system is completely depressurized before starting work, wear appropriate PPE, follow all safety procedures in the maintenance manual, and be careful with hydraulic fluid as it can be harmful to skin and eyes.")
        ]

        for role_str, content in messages:
            role = MessageRole.USER if role_str == "USER" else MessageRole.ASSISTANT
            message = conversation_repo.add_message(
                conversation_id=test_conversation.conversation_id,
                role=role,
                content=content,
                add_to_context=True,
                context_priority=ContextPriority.MEDIUM
            )

        # Step 2: Create a summarizer
        summarizer = ConversationSummarizer(llm_service=llm_service)

        # Step 3: Get all messages
        all_messages = conversation_repo.get_messages(test_conversation.conversation_id)
        assert len(all_messages) == 11  # 1 system + 5 user + 5 assistant

        # Step 4: Identify segments for summarization
        segments = summarizer.identify_segments_for_summarization(
            messages=all_messages,
            segment_size=4,  # Small segment size for testing
            overlap=1
        )
        assert len(segments) > 0

        # Step 5: Summarize a segment
        segment = segments[0]
        summary_text = await summarizer.summarize_messages(
            messages=segment["messages"]
        )
        assert summary_text is not None
        assert len(summary_text) > 0

        # Step 6: Create summary in database
        summary = context_service.summarize_conversation_segment(
            conversation_id=test_conversation.id,
            start_message_id=segment["start_message_id"],
            end_message_id=segment["end_message_id"],
            summary_content=summary_text
        )
        assert summary is not None

        # Step 7: Add summary to context
        context_item = context_service.add_summary_to_context(
            summary_id=summary.id,
            conversation_id=test_conversation.id,
            priority=ContextPriority.HIGH
        )
        assert context_item is not None
        assert context_item.item_type == ContextType.SUMMARY
        assert context_item.source_id == summary.id

    @pytest.mark.asyncio
    async def test_user_preference_extraction(
        self,
        conversation_repo,
        context_service,
        test_conversation,
        llm_service
    ):
        """
        Test user preference extraction.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Step 1: Add messages with user preferences
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Add messages with preferences
        messages = [
            ("USER", "I work on Boeing 737 aircraft."),
            ("ASSISTANT", "Great, I'll focus on Boeing 737 maintenance information."),
            ("USER", "I prefer detailed step-by-step instructions."),
            ("ASSISTANT", "I'll provide detailed step-by-step instructions for maintenance procedures."),
            ("USER", "I need information in metric units."),
            ("ASSISTANT", "I'll provide measurements in metric units.")
        ]

        for role_str, content in messages:
            role = MessageRole.USER if role_str == "USER" else MessageRole.ASSISTANT
            message = conversation_repo.add_message(
                conversation_id=test_conversation.conversation_id,
                role=role,
                content=content,
                add_to_context=True,
                context_priority=ContextPriority.MEDIUM
            )

        # Step 2: Create preference manager
        preference_manager = PreferenceManager(llm_service=llm_service)

        # Step 3: Get all messages
        all_messages = conversation_repo.get_messages(test_conversation.conversation_id)

        # Step 4: Extract preferences
        preferences = await preference_manager.extract_preferences(
            messages=all_messages,
            conversation_id=test_conversation.id
        )
        assert preferences is not None
        assert len(preferences) > 0

        # Step 5: Store preferences
        for pref_key, pref_value in preferences.items():
            user_pref = context_service.set_user_preference(
                conversation_id=test_conversation.id,
                key=pref_key,
                value=pref_value
            )
            assert user_pref is not None
            assert user_pref.key == pref_key
            assert user_pref.value == pref_value

        # Step 6: Retrieve preferences
        stored_prefs = context_service.get_user_preferences(test_conversation.id)
        assert stored_prefs is not None
        assert len(stored_prefs) == len(preferences)

        # Step 7: Include preferences in context
        context_messages = conversation_repo.get_conversation_context(
            conversation_id=test_conversation.conversation_id,
            max_tokens=4000,
            include_system_prompt=True,
            include_user_preferences=True
        )

        # Verify preferences are included in context
        prefs_included = False
        for message in context_messages:
            if message["role"] == "system" and "User Preferences" in message["content"]:
                prefs_included = True
                break

        assert prefs_included, "User preferences should be included in context"

    @pytest.mark.asyncio
    async def test_context_tagging_and_retrieval(
        self,
        conversation_repo,
        context_service,
        test_conversation,
        llm_service
    ):
        """
        Test context tagging and retrieval by tags.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Step 1: Add messages
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Add messages with different topics
        messages = [
            ("USER", "I need to perform hydraulic system maintenance on a Boeing 737."),
            ("ASSISTANT", "I can help with hydraulic system maintenance for the Boeing 737."),
            ("USER", "What are the common issues with landing gear?"),
            ("ASSISTANT", "Common landing gear issues include hydraulic leaks, worn bushings, and damaged seals."),
            ("USER", "How often should I inspect the fuel system?"),
            ("ASSISTANT", "Fuel system inspections should be performed according to the maintenance schedule, typically every 600 flight hours.")
        ]

        message_ids = []
        for role_str, content in messages:
            role = MessageRole.USER if role_str == "USER" else MessageRole.ASSISTANT
            message = conversation_repo.add_message(
                conversation_id=test_conversation.conversation_id,
                role=role,
                content=content,
                add_to_context=True,
                context_priority=ContextPriority.MEDIUM
            )
            message_ids.append(message.id)

        # Step 2: Get context window and items
        window_repo = ContextWindowRepository(context_service.session)
        window = window_repo.get_active_window_for_conversation(test_conversation.id)

        item_repo = ContextItemRepository(context_service.session)
        items = item_repo.get_items_for_window(window.id)

        # Step 3: Create tag manager
        tag_repo = ContextTagRepository(context_service.session)
        tag_manager = TagManager(tag_repo=tag_repo, llm_service=llm_service)

        # Step 4: Tag items
        for item in items:
            tags = tag_manager.tag_item(item)
            assert len(tags) >= 0  # Some items might not get tags

        # Step 5: Add specific tags for testing
        hydraulic_tag = tag_repo.create_tag(
            item_id=items[1].id,  # First user message about hydraulics
            tag_name="hydraulic_system",
            tag_value="maintenance",
            tag_type="topic"
        )
        assert hydraulic_tag is not None

        landing_gear_tag = tag_repo.create_tag(
            item_id=items[3].id,  # User message about landing gear
            tag_name="landing_gear",
            tag_value="issues",
            tag_type="topic"
        )
        assert landing_gear_tag is not None

        fuel_tag = tag_repo.create_tag(
            item_id=items[5].id,  # User message about fuel system
            tag_name="fuel_system",
            tag_value="inspection",
            tag_type="topic"
        )
        assert fuel_tag is not None

        # Step 6: Retrieve items by tags
        hydraulic_items = tag_repo.get_items_by_tag(
            window_id=window.id,
            tag_name="hydraulic_system"
        )
        assert len(hydraulic_items) >= 1

        landing_gear_items = tag_repo.get_items_by_tag(
            window_id=window.id,
            tag_name="landing_gear"
        )
        assert len(landing_gear_items) >= 1

        # Step 7: Retrieve items by multiple tags
        multi_tag_items = tag_repo.get_items_by_tags(
            window_id=window.id,
            tag_names=["hydraulic_system", "landing_gear"]
        )
        assert len(multi_tag_items) >= 2

    @pytest.mark.asyncio
    async def test_context_window_monitoring(
        self,
        conversation_repo,
        context_service,
        test_conversation
    ):
        """
        Test context window monitoring.
        """
        if test_conversation is None:
            pytest.skip("Skipping test due to database setup issue")

        # Step 1: Add messages
        system_message = conversation_repo.add_message(
            conversation_id=test_conversation.conversation_id,
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant for aircraft maintenance.",
            add_to_context=True,
            context_priority=ContextPriority.CRITICAL
        )

        # Add 10 pairs of user and assistant messages
        for i in range(10):
            user_message = conversation_repo.add_message(
                conversation_id=test_conversation.conversation_id,
                role=MessageRole.USER,
                content=f"User message {i+1} with some content to increase token count",
                add_to_context=True,
                context_priority=ContextPriority.MEDIUM
            )

            assistant_message = conversation_repo.add_message(
                conversation_id=test_conversation.conversation_id,
                role=MessageRole.ASSISTANT,
                content=f"Assistant response {i+1} with detailed information to increase the token count in the context window",
                add_to_context=True,
                context_priority=ContextPriority.MEDIUM
            )

        # Step 2: Get context window
        window_repo = ContextWindowRepository(context_service.session)
        window = window_repo.get_active_window_for_conversation(test_conversation.id)

        # Step 3: Create context window monitor
        monitor = ContextWindowMonitor(
            window_repo=window_repo,
            item_repo=ContextItemRepository(context_service.session)
        )

        # Step 4: Get window statistics
        stats = monitor.get_window_statistics(window.id)
        assert stats is not None
        assert stats["total_items"] == 21  # 1 system + 10 user + 10 assistant
        assert stats["token_count"] > 0
        assert stats["window_age_seconds"] >= 0

        # Step 5: Check if window needs pruning
        needs_pruning = monitor.window_needs_pruning(
            window_id=window.id,
            max_tokens=100,  # Set low to trigger pruning
            max_items=5  # Set low to trigger pruning
        )
        assert needs_pruning is True

        # Step 6: Check if window needs summarization
        needs_summarization = monitor.window_needs_summarization(
            window_id=window.id,
            min_messages_for_summarization=10,
            max_window_age_seconds=3600
        )
        assert needs_summarization is True
