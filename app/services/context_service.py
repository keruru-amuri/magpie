"""
Context management service for the MAGPIE platform.
"""
import logging
from typing import Dict, List, Optional, Union, Tuple, Any

from sqlalchemy.orm import Session

from app.core.db.connection import DatabaseConnectionFactory
from app.models.context import (
    ContextWindow, ContextItem, ContextTag, ContextSummary,
    ContextType, ContextPriority, UserPreference
)
from app.models.conversation import Conversation, Message, MessageRole
from app.repositories.context import (
    ContextWindowRepository, ContextItemRepository,
    ContextTagRepository, ContextSummaryRepository,
    UserPreferenceRepository
)
from app.repositories.conversation import ConversationRepository
from app.services.token_utils import count_tokens_approximate

# Configure logging
logger = logging.getLogger(__name__)


class ContextService:
    """
    Service for context management operations.
    """

    def __init__(self, session: Optional[Session] = None, llm_service: Optional[Any] = None):
        """
        Initialize context service.

        Args:
            session: SQLAlchemy session
            llm_service: LLM service for summarization and tagging
        """
        self.session = session or DatabaseConnectionFactory.get_session()
        self.window_repo = ContextWindowRepository(self.session)
        self.item_repo = ContextItemRepository(self.session)
        self.tag_repo = ContextTagRepository(self.session)
        self.summary_repo = ContextSummaryRepository(self.session)
        self.preference_repo = UserPreferenceRepository(self.session)
        self.conversation_repo = ConversationRepository(self.session)

        # Initialize LLM service if provided
        if llm_service:
            self.llm_service = llm_service
        else:
            # Import here to avoid circular imports
            from app.services.llm_service import LLMService
            self.llm_service = LLMService()

    def add_message_to_context(
        self,
        conversation_id: Union[int, str],
        message: Union[Message, Dict[str, Any]],
        priority: ContextPriority = ContextPriority.MEDIUM
    ) -> Optional[ContextItem]:
        """
        Add a message to the context.

        Args:
            conversation_id: Conversation ID
            message: Message object or dictionary with message data
            priority: Priority level

        Returns:
            Optional[ContextItem]: Created context item or None if error
        """
        try:
            # Get active context window
            window = self.window_repo.get_active_window_for_conversation(conversation_id)
            if not window:
                logger.error(f"Failed to get or create context window for conversation {conversation_id}")
                return None

            # Handle message object or dictionary
            if isinstance(message, dict):
                # Create message from dictionary
                role = message.get("role", MessageRole.USER)
                content = message.get("content", "")
                meta_data = message.get("meta_data")

                # Get conversation
                conversation = None
                if isinstance(conversation_id, str):
                    conversation = self.conversation_repo.get_by_conversation_id(conversation_id)
                else:
                    conversation = self.session.get(Conversation, conversation_id)

                if not conversation:
                    logger.error(f"Conversation not found: {conversation_id}")
                    return None

                # Create message
                message = Message(
                    conversation_id=conversation.id,
                    role=role,
                    content=content,
                    meta_data=meta_data
                )
                self.session.add(message)
                self.session.flush()

            # Add message to context
            context_item = self.item_repo.add_message_to_context(
                window_id=window.id,
                message_id=message.id,
                priority=priority
            )

            return context_item
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding message to context: {str(e)}")
            return None

    def get_context_for_conversation(
        self,
        conversation_id: Union[int, str],
        max_tokens: int = 4000,
        include_system_prompt: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get context for a conversation formatted for LLM input.

        Args:
            conversation_id: Conversation ID
            max_tokens: Maximum number of tokens to include
            include_system_prompt: Whether to include system prompt

        Returns:
            List[Dict[str, Any]]: List of context messages formatted for LLM input
        """
        try:
            # Get active context window
            window = self.window_repo.get_active_window_for_conversation(conversation_id)
            if not window:
                logger.error(f"Failed to get or create context window for conversation {conversation_id}")
                return []

            # Get context items
            items = self.item_repo.get_items_for_window(
                window_id=window.id,
                included_only=True
            )

            # Sort items by priority and position
            items.sort(
                key=lambda x: (
                    # Sort by priority (HIGH to LOW)
                    {
                        ContextPriority.CRITICAL: 0,
                        ContextPriority.HIGH: 1,
                        ContextPriority.MEDIUM: 2,
                        ContextPriority.LOW: 3
                    }.get(x.priority, 4),
                    # Then by position
                    x.position
                )
            )

            # Format items for LLM input
            context_messages = []
            current_tokens = 0

            # Add system prompt if requested
            if include_system_prompt:
                # Find system prompt in context items
                system_items = [
                    item for item in items
                    if item.context_type == ContextType.SYSTEM
                ]

                if system_items:
                    # Use the highest priority system item
                    system_item = max(
                        system_items,
                        key=lambda x: (
                            {
                                ContextPriority.CRITICAL: 3,
                                ContextPriority.HIGH: 2,
                                ContextPriority.MEDIUM: 1,
                                ContextPriority.LOW: 0
                            }.get(x.priority, 0)
                        )
                    )

                    system_content = system_item.content
                    if system_item.message_id:
                        message = self.session.get(Message, system_item.message_id)
                        if message:
                            system_content = message.content

                    if system_content:
                        system_tokens = count_tokens_approximate(system_content)
                        if current_tokens + system_tokens <= max_tokens:
                            context_messages.append({
                                "role": "system",
                                "content": system_content
                            })
                            current_tokens += system_tokens

            # Process remaining items
            for item in items:
                # Skip system items if already processed
                if item.context_type == ContextType.SYSTEM and include_system_prompt:
                    continue

                # Get content
                content = item.content
                role = "system"  # Default role

                if item.message_id:
                    # Get content from message
                    message = self.session.get(Message, item.message_id)
                    if message:
                        content = message.content
                        role = message.role.value

                # Skip if no content
                if not content:
                    continue

                # Check token limit
                item_tokens = count_tokens_approximate(content)
                if current_tokens + item_tokens > max_tokens:
                    # Skip this item if it would exceed the token limit
                    continue

                # Add to context messages
                context_messages.append({
                    "role": role,
                    "content": content
                })
                current_tokens += item_tokens

            return context_messages
        except Exception as e:
            logger.error(f"Error getting context for conversation: {str(e)}")
            return []

    def prune_context(
        self,
        conversation_id: Union[int, str],
        max_tokens: int = 4000,
        preserve_types: Optional[List[ContextType]] = None,
        preserve_priorities: Optional[List[ContextPriority]] = None
    ) -> bool:
        """
        Prune context to fit within token limit.

        Args:
            conversation_id: Conversation ID
            max_tokens: Maximum number of tokens to keep
            preserve_types: Context types to preserve
            preserve_priorities: Priority levels to preserve

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get active context window
            window = self.window_repo.get_active_window_for_conversation(conversation_id)
            if not window:
                logger.error(f"Failed to get or create context window for conversation {conversation_id}")
                return False

            # Check if pruning is needed
            if window.current_tokens <= max_tokens:
                return True

            # Get context items
            items = self.item_repo.get_items_for_window(
                window_id=window.id,
                included_only=True
            )

            # Set default preserve types and priorities if not provided
            if preserve_types is None:
                preserve_types = [ContextType.SYSTEM, ContextType.USER_PREFERENCE]

            if preserve_priorities is None:
                preserve_priorities = [ContextPriority.CRITICAL, ContextPriority.HIGH]

            # Sort items by pruning priority (items to prune first come first)
            items.sort(
                key=lambda x: (
                    # Preserve specified types
                    0 if x.context_type in preserve_types else 1,
                    # Preserve specified priorities
                    0 if x.priority in preserve_priorities else 1,
                    # Prefer higher priorities
                    {
                        ContextPriority.CRITICAL: 0,
                        ContextPriority.HIGH: 1,
                        ContextPriority.MEDIUM: 2,
                        ContextPriority.LOW: 3
                    }.get(x.priority, 4),
                    # Prefer newer items (higher position)
                    -x.position
                )
            )

            # Calculate tokens to remove
            tokens_to_remove = window.current_tokens - max_tokens

            # Prune items
            for item in items:
                # Skip items with preserved types and priorities
                if (item.context_type in preserve_types and
                        item.priority in preserve_priorities):
                    continue

                # Exclude item from context
                self.item_repo.update_item_inclusion(
                    item_id=item.id,
                    is_included=False
                )

                # Update tokens to remove
                tokens_to_remove -= item.token_count

                # Check if we've removed enough tokens
                if tokens_to_remove <= 0:
                    break

            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error pruning context: {str(e)}")
            return False

    async def summarize_conversation_segment(
        self,
        conversation_id: Union[int, str],
        start_message_id: Optional[int] = None,
        end_message_id: Optional[int] = None,
        summary_content: Optional[str] = None
    ) -> Optional[ContextSummary]:
        """
        Create a summary of a conversation segment.

        Args:
            conversation_id: Conversation ID
            start_message_id: Start message ID
            end_message_id: End message ID
            summary_content: Summary content (if None, will be generated)

        Returns:
            Optional[ContextSummary]: Created summary or None if error
        """
        try:
            # Get conversation
            conversation = None
            if isinstance(conversation_id, str):
                conversation = self.conversation_repo.get_by_conversation_id(conversation_id)
            else:
                conversation = self.session.get(Conversation, conversation_id)

            if not conversation:
                logger.error(f"Conversation not found: {conversation_id}")
                return None

            # If summary content is not provided, generate it
            if not summary_content:
                # Get messages in the segment
                messages = []
                if start_message_id and end_message_id:
                    # Get messages between start and end
                    messages = self.conversation_repo.get_messages_in_range(
                        conversation_id=conversation.id,
                        start_id=start_message_id,
                        end_id=end_message_id
                    )
                else:
                    # Get all messages
                    messages = self.conversation_repo.get_messages(
                        conversation_id=conversation.id
                    )

                if not messages:
                    logger.error(f"No messages found for summarization")
                    return None

                # Generate summary using LLM
                from app.core.context.summarization import ConversationSummarizer
                from app.services.llm_service import LLMService

                llm_service = LLMService()
                summarizer = ConversationSummarizer(llm_service)

                try:
                    summary_content = await summarizer.summarize_messages(messages)
                except Exception as e:
                    logger.error(f"Error generating summary with LLM: {str(e)}")
                    # Fallback to a placeholder summary
                    summary_content = f"Summary of conversation segment with {len(messages)} messages"

            # Create summary
            summary = self.summary_repo.create_summary(
                conversation_id=conversation.id,
                summary_content=summary_content,
                start_message_id=start_message_id,
                end_message_id=end_message_id
            )

            # Add metadata tags to the summary
            try:
                from app.core.context.tagging import TagManager
                tag_manager = TagManager(self.tag_repo)

                # Create a mock context item for tagging
                mock_item = ContextItem(
                    id=-1,  # Temporary ID
                    context_window_id=-1,  # Temporary ID
                    content=summary_content,
                    context_type=ContextType.SUMMARY,
                    token_count=0,
                    priority=ContextPriority.MEDIUM,
                    position=0,
                    is_included=True
                )

                # Tag the summary content
                tag_manager.tag_item_complete(mock_item, use_llm=True)

                # Add the tags to the actual summary
                for tag in mock_item.tags:
                    self.tag_repo.add_tag(
                        item_id=summary.id,
                        key=tag.tag_key,
                        value=tag.tag_value
                    )
            except Exception as e:
                logger.error(f"Error tagging summary: {str(e)}")
                # Continue without tagging

            return summary
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error summarizing conversation segment: {str(e)}")
            return None

    def add_summary_to_context(
        self,
        summary_id: int,
        conversation_id: Union[int, str],
        priority: ContextPriority = ContextPriority.HIGH
    ) -> Optional[ContextItem]:
        """
        Add a summary to the context.

        Args:
            summary_id: Summary ID
            conversation_id: Conversation ID
            priority: Priority level

        Returns:
            Optional[ContextItem]: Created context item or None if error
        """
        try:
            # Get active context window
            window = self.window_repo.get_active_window_for_conversation(conversation_id)
            if not window:
                logger.error(f"Failed to get or create context window for conversation {conversation_id}")
                return None

            # Add summary to context
            result = self.summary_repo.add_summary_to_context(
                summary_id=summary_id,
                window_id=window.id,
                priority=priority
            )

            if not result:
                return None

            return result[1]  # Return the context item
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding summary to context: {str(e)}")
            return None

    def extract_user_preference(
        self,
        message_id: int,
        key: str,
        value: str,
        confidence: float = 1.0
    ) -> Optional[UserPreference]:
        """
        Extract a user preference from a message.

        Args:
            message_id: Message ID
            key: Preference key
            value: Preference value
            confidence: Confidence level

        Returns:
            Optional[UserPreference]: Created preference or None if error
        """
        try:
            # Get message
            message = self.session.get(Message, message_id)
            if not message:
                logger.error(f"Message not found: {message_id}")
                return None

            # Get conversation
            conversation = self.session.get(Conversation, message.conversation_id)
            if not conversation:
                logger.error(f"Conversation not found for message: {message_id}")
                return None

            # Set preference
            preference = self.preference_repo.set_preference(
                user_id=conversation.user_id,
                key=key,
                value=value,
                confidence=confidence,
                source_message_id=message_id
            )

            return preference
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error extracting user preference: {str(e)}")
            return None

    def add_user_preferences_to_context(
        self,
        conversation_id: Union[int, str],
        priority: ContextPriority = ContextPriority.HIGH,
        keys: Optional[List[str]] = None
    ) -> List[ContextItem]:
        """
        Add user preferences to the context.

        Args:
            conversation_id: Conversation ID
            priority: Priority level
            keys: Optional list of preference keys to include

        Returns:
            List[ContextItem]: List of created context items
        """
        try:
            # Get conversation
            conversation = None
            if isinstance(conversation_id, str):
                conversation = self.conversation_repo.get_by_conversation_id(conversation_id)
            else:
                conversation = self.session.get(Conversation, conversation_id)

            if not conversation:
                logger.error(f"Conversation not found: {conversation_id}")
                return []

            # Get active context window
            window = self.window_repo.get_active_window_for_conversation(conversation_id)
            if not window:
                logger.error(f"Failed to get or create context window for conversation {conversation_id}")
                return []

            # Add preferences to context
            context_items = self.preference_repo.add_preferences_to_context(
                user_id=conversation.user_id,
                window_id=window.id,
                priority=priority,
                keys=keys
            )

            return context_items
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding user preferences to context: {str(e)}")
            return []

    def add_system_prompt_to_context(
        self,
        conversation_id: Union[int, str],
        system_prompt: str,
        priority: ContextPriority = ContextPriority.CRITICAL
    ) -> Optional[ContextItem]:
        """
        Add a system prompt to the context.

        Args:
            conversation_id: Conversation ID
            system_prompt: System prompt content
            priority: Priority level

        Returns:
            Optional[ContextItem]: Created context item or None if error
        """
        try:
            # Get active context window
            window = self.window_repo.get_active_window_for_conversation(conversation_id)
            if not window:
                logger.error(f"Failed to get or create context window for conversation {conversation_id}")
                return None

            # Add system prompt to context
            context_item = self.item_repo.add_content_to_context(
                window_id=window.id,
                content=system_prompt,
                context_type=ContextType.SYSTEM,
                priority=priority,
                position=0  # Always at the beginning
            )

            return context_item
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding system prompt to context: {str(e)}")
            return None

    def clear_context(self, conversation_id: Union[int, str]) -> bool:
        """
        Clear the context for a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get active context window
            window = self.window_repo.get_active_window_for_conversation(conversation_id)
            if not window:
                logger.error(f"Failed to get or create context window for conversation {conversation_id}")
                return False

            # Get all context items
            items = self.item_repo.get_items_for_window(
                window_id=window.id,
                included_only=False
            )

            # Delete all items
            for item in items:
                self.item_repo.delete_by_id(item.id)

            # Reset window token count
            window.current_tokens = 0
            self.session.flush()

            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error clearing context: {str(e)}")
            return False
