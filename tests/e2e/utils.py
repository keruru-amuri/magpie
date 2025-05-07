"""
Utility functions for end-to-end tests.
"""
import asyncio
import json
import random
import string
import uuid
from typing import Dict, List, Optional, Any, Union

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


def random_string(length: int = 10) -> str:
    """Generate a random string of fixed length."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


def create_test_conversation(
    conversation_repo: ConversationRepository,
    user_id: int,
    agent_type: AgentType = AgentType.DOCUMENTATION,
    title: Optional[str] = None
) -> Conversation:
    """
    Create a test conversation.

    Args:
        conversation_repo: Conversation repository
        user_id: User ID
        agent_type: Agent type
        title: Conversation title

    Returns:
        Conversation: Created conversation
    """
    if title is None:
        title = f"Test Conversation {random_string(8)}"

    conversation_data = {
        "user_id": user_id,
        "title": title,
        "agent_type": agent_type
    }

    return conversation_repo.create(conversation_data)


def add_test_messages(
    conversation_repo: ConversationRepository,
    conversation_id: Union[str, uuid.UUID],
    message_pairs: List[Dict[str, str]]
) -> List[Message]:
    """
    Add test message pairs to a conversation.

    Args:
        conversation_repo: Conversation repository
        conversation_id: Conversation ID
        message_pairs: List of message pairs, each containing 'user' and 'assistant' keys

    Returns:
        List[Message]: Created messages
    """
    messages = []

    for pair in message_pairs:
        user_message = conversation_repo.add_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=pair["user"],
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )
        messages.append(user_message)

        assistant_message = conversation_repo.add_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=pair["assistant"],
            add_to_context=True,
            context_priority=ContextPriority.MEDIUM
        )
        messages.append(assistant_message)

    return messages


def add_system_message(
    conversation_repo: ConversationRepository,
    conversation_id: Union[str, uuid.UUID],
    content: str = "You are a helpful assistant for aircraft maintenance."
) -> Message:
    """
    Add a system message to a conversation.

    Args:
        conversation_repo: Conversation repository
        conversation_id: Conversation ID
        content: System message content

    Returns:
        Message: Created system message
    """
    return conversation_repo.add_message(
        conversation_id=conversation_id,
        role=MessageRole.SYSTEM,
        content=content,
        add_to_context=True,
        context_priority=ContextPriority.CRITICAL
    )


def create_test_context_window(
    context_service: ContextService,
    conversation_id: Union[int, str, uuid.UUID]
) -> ContextWindow:
    """
    Create a test context window.

    Args:
        context_service: Context service
        conversation_id: Conversation ID

    Returns:
        ContextWindow: Created context window
    """
    return context_service.create_new_window(conversation_id)


def add_test_context_items(
    context_service: ContextService,
    window_id: int,
    items: List[Dict[str, Any]]
) -> List[ContextItem]:
    """
    Add test context items to a window.

    Args:
        context_service: Context service
        window_id: Context window ID
        items: List of item data dictionaries

    Returns:
        List[ContextItem]: Created context items
    """
    item_repo = ContextItemRepository(context_service.session)
    created_items = []

    for item_data in items:
        item = item_repo.create_item(
            window_id=window_id,
            item_type=item_data.get("item_type", ContextType.MESSAGE),
            source_id=item_data.get("source_id"),
            priority=item_data.get("priority", ContextPriority.MEDIUM),
            metadata=item_data.get("metadata")
        )
        created_items.append(item)

    return created_items


def add_test_user_preferences(
    context_service: ContextService,
    conversation_id: Union[int, str, uuid.UUID],
    preferences: Dict[str, str]
) -> List[UserPreference]:
    """
    Add test user preferences.

    Args:
        context_service: Context service
        conversation_id: Conversation ID
        preferences: Dictionary of preference key-value pairs

    Returns:
        List[UserPreference]: Created user preferences
    """
    created_prefs = []

    for key, value in preferences.items():
        pref = context_service.set_user_preference(
            conversation_id=conversation_id,
            key=key,
            value=value
        )
        created_prefs.append(pref)

    return created_prefs


def add_test_context_tags(
    context_service: ContextService,
    item_id: int,
    tags: List[Dict[str, str]]
) -> List[ContextTag]:
    """
    Add test context tags.

    Args:
        context_service: Context service
        item_id: Context item ID
        tags: List of tag dictionaries with 'name', 'value', and 'type' keys

    Returns:
        List[ContextTag]: Created context tags
    """
    tag_repo = ContextTagRepository(context_service.session)
    created_tags = []

    for tag_data in tags:
        tag = tag_repo.create_tag(
            item_id=item_id,
            tag_name=tag_data.get("name"),
            tag_value=tag_data.get("value", ""),
            tag_type=tag_data.get("type", "topic")
        )
        created_tags.append(tag)

    return created_tags


def create_test_summary(
    context_service: ContextService,
    conversation_id: Union[int, str, uuid.UUID],
    start_message_id: int,
    end_message_id: int,
    summary_content: str
) -> ContextSummary:
    """
    Create a test context summary.

    Args:
        context_service: Context service
        conversation_id: Conversation ID
        start_message_id: Start message ID
        end_message_id: End message ID
        summary_content: Summary content

    Returns:
        ContextSummary: Created context summary
    """
    return context_service.summarize_conversation_segment(
        conversation_id=conversation_id,
        start_message_id=start_message_id,
        end_message_id=end_message_id,
        summary_content=summary_content
    )


def add_summary_to_context(
    context_service: ContextService,
    summary_id: int,
    conversation_id: Union[int, str, uuid.UUID],
    priority: ContextPriority = ContextPriority.HIGH
) -> ContextItem:
    """
    Add a summary to context.

    Args:
        context_service: Context service
        summary_id: Summary ID
        conversation_id: Conversation ID
        priority: Context priority

    Returns:
        ContextItem: Created context item
    """
    return context_service.add_summary_to_context(
        summary_id=summary_id,
        conversation_id=conversation_id,
        priority=priority
    )


def get_window_statistics(
    context_service: ContextService,
    window_id: int
) -> Dict[str, Any]:
    """
    Get statistics for a context window.

    Args:
        context_service: Context service
        window_id: Context window ID

    Returns:
        Dict[str, Any]: Window statistics
    """
    from app.core.context.monitoring import ContextWindowMonitor
    
    window_repo = ContextWindowRepository(context_service.session)
    item_repo = ContextItemRepository(context_service.session)
    
    monitor = ContextWindowMonitor(
        window_repo=window_repo,
        item_repo=item_repo
    )
    
    return monitor.get_window_statistics(window_id)


async def process_agent_query(
    agent_factory: AgentFactory,
    agent_type: AgentType,
    query: str,
    conversation_id: Union[str, uuid.UUID],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process a query with an agent.

    Args:
        agent_factory: Agent factory
        agent_type: Agent type
        query: Query string
        conversation_id: Conversation ID
        context: Context dictionary

    Returns:
        Dict[str, Any]: Agent response
    """
    agent = agent_factory.create_agent(agent_type)
    return await agent.process_query(
        query=query,
        conversation_id=str(conversation_id),
        context=context
    )


def simulate_conversation(
    conversation_repo: ConversationRepository,
    context_service: ContextService,
    agent_factory: AgentFactory,
    conversation_id: Union[str, uuid.UUID],
    agent_type: AgentType,
    messages: List[str]
) -> List[Dict[str, Any]]:
    """
    Simulate a conversation with an agent.

    Args:
        conversation_repo: Conversation repository
        context_service: Context service
        agent_factory: Agent factory
        conversation_id: Conversation ID
        agent_type: Agent type
        messages: List of user message strings

    Returns:
        List[Dict[str, Any]]: List of agent responses
    """
    # Create event loop if needed
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    agent = agent_factory.create_agent(agent_type)
    responses = []
    
    for message in messages:
        # Add user message
        user_message = conversation_repo.add_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=message,
            add_to_context=True,
            context_priority=ContextPriority.HIGH
        )
        
        # Get context messages
        context_messages = conversation_repo.get_conversation_context(
            conversation_id=conversation_id,
            max_tokens=4000,
            include_system_prompt=True
        )
        
        # Create context
        context = {
            "conversation_history": context_messages,
            "aircraft_type": "Boeing 737"  # Default aircraft type
        }
        
        # Process query
        result = loop.run_until_complete(agent.process_query(
            query=message,
            conversation_id=str(conversation_id),
            context=context
        ))
        
        # Add assistant message
        assistant_message = conversation_repo.add_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=result["response"],
            add_to_context=True,
            context_priority=ContextPriority.MEDIUM
        )
        
        responses.append(result)
    
    return responses
"""
