"""
Conversation repository for the MAGPIE platform.
"""
import logging
import uuid
from typing import Dict, List, Optional, Union, Tuple

from sqlalchemy import select, and_, or_, desc, between
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.models.conversation import AgentType, Conversation, Message, MessageRole
from app.models.context import ContextWindow, ContextItem, ContextType, ContextPriority
from app.repositories.base import BaseRepository
from app.repositories.context import ContextWindowRepository, ContextItemRepository

# Configure logging
logger = logging.getLogger(__name__)


class ConversationRepository(BaseRepository[Conversation]):
    """
    Repository for Conversation model.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(Conversation, session)

    def get_by_conversation_id(self, conversation_id: Union[str, uuid.UUID]) -> Optional[Conversation]:
        """
        Get conversation by conversation_id.

        Args:
            conversation_id: Conversation UUID

        Returns:
            Optional[Conversation]: Conversation or None if not found
        """
        try:
            # Convert string to UUID if needed
            if isinstance(conversation_id, str):
                conversation_id = uuid.UUID(conversation_id)

            query = select(Conversation).where(Conversation.conversation_id == conversation_id)
            result = self.session.execute(query)
            return result.scalar_one_or_none()
        except (SQLAlchemyError, ValueError) as e:
            logger.error(f"Error getting conversation by conversation_id: {str(e)}")
            return None

    def get_by_user_id(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0,
        agent_type: Optional[AgentType] = None,
        active_only: bool = True
    ) -> List[Conversation]:
        """
        Get conversations by user ID.

        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip
            agent_type: Filter by agent type
            active_only: Only return active conversations

        Returns:
            List[Conversation]: List of conversations
        """
        try:
            query = select(Conversation).where(Conversation.user_id == user_id)

            # Apply filters
            if agent_type:
                query = query.where(Conversation.agent_type == agent_type)

            if active_only:
                query = query.where(Conversation.is_active == True)

            # Apply pagination and ordering
            query = (
                query
                .order_by(desc(Conversation.updated_at))
                .limit(limit)
                .offset(offset)
            )

            result = self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting conversations by user ID: {str(e)}")
            return []

    def get_with_messages(
        self,
        conversation_id: Union[str, uuid.UUID],
        limit: int = 100,
        offset: int = 0
    ) -> Optional[Conversation]:
        """
        Get conversation with messages.

        Args:
            conversation_id: Conversation UUID
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            Optional[Conversation]: Conversation with messages or None if not found
        """
        try:
            # Convert string to UUID if needed
            if isinstance(conversation_id, str):
                conversation_id = uuid.UUID(conversation_id)

            # Get conversation with eager loading of messages
            query = (
                select(Conversation)
                .where(Conversation.conversation_id == conversation_id)
                .options(joinedload(Conversation.messages))
            )

            result = self.session.execute(query)
            conversation = result.scalar_one_or_none()

            if conversation:
                # Sort messages by created_at
                conversation.messages.sort(key=lambda m: m.created_at)

                # Apply pagination if needed
                if limit > 0:
                    conversation.messages = conversation.messages[offset:offset+limit]

            return conversation
        except (SQLAlchemyError, ValueError) as e:
            logger.error(f"Error getting conversation with messages: {str(e)}")
            return None

    def search_conversations(
        self,
        user_id: int,
        search_term: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Conversation]:
        """
        Search conversations by title.

        Args:
            user_id: User ID
            search_term: Search term
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip

        Returns:
            List[Conversation]: List of matching conversations
        """
        try:
            # Create search pattern
            pattern = f"%{search_term}%"

            # Search in conversation title and messages
            query = (
                select(Conversation)
                .distinct()
                .join(Conversation.messages)
                .where(
                    and_(
                        Conversation.user_id == user_id,
                        or_(
                            Conversation.title.ilike(pattern),
                            Message.content.ilike(pattern)
                        )
                    )
                )
                .order_by(desc(Conversation.updated_at))
                .limit(limit)
                .offset(offset)
            )

            result = self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error searching conversations: {str(e)}")
            return []

    def add_message(
        self,
        conversation_id: Union[int, str, uuid.UUID],
        role: MessageRole,
        content: str,
        meta_data: Optional[Dict] = None,
        add_to_context: bool = True,
        context_priority: ContextPriority = ContextPriority.MEDIUM,
        extract_preferences: bool = True
    ) -> Optional[Message]:
        """
        Add message to conversation.

        Args:
            conversation_id: Conversation ID or UUID
            role: Message role
            content: Message content
            meta_data: Message metadata
            add_to_context: Whether to add the message to the context window
            context_priority: Priority level for the message in the context window
            extract_preferences: Whether to extract user preferences from the message

        Returns:
            Optional[Message]: Created message or None if error
        """
        try:
            # Get conversation
            conversation = None

            if isinstance(conversation_id, (str, uuid.UUID)):
                conversation = self.get_by_conversation_id(conversation_id)
            else:
                conversation = self.get_by_id(conversation_id)

            if not conversation:
                return None

            # Create message
            message = Message(
                conversation_id=conversation.id,
                role=role,
                content=content,
                meta_data=meta_data
            )

            # Add to session and flush to get ID
            self.session.add(message)
            self.session.flush()

            # Update conversation updated_at
            conversation.updated_at = message.created_at
            self.session.flush()

            # Add to context if requested
            if add_to_context:
                self.add_message_to_context(message.id, context_priority)

            # Extract preferences if requested and it's a user message
            if extract_preferences and role == MessageRole.USER:
                # Schedule preference extraction asynchronously
                # This is done in a background task to avoid blocking the request
                try:
                    import asyncio
                    from app.core.context.preference_extraction import PreferenceManager
                    from app.services.context_service import ContextService

                    # Create a background task for preference extraction
                    async def extract_preferences_task():
                        try:
                            context_service = ContextService()
                            preference_manager = PreferenceManager(context_service)
                            await preference_manager.process_message(message)
                        except Exception as e:
                            logger.error(f"Error in preference extraction task: {str(e)}")

                    # Run the task in the background
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        # Create a new event loop if none exists
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    # Schedule the task
                    loop.create_task(extract_preferences_task())
                except Exception as e:
                    logger.error(f"Error scheduling preference extraction: {str(e)}")

            # Update cache
            self._cache_set(conversation)

            return message
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error adding message to conversation: {str(e)}")
            return None

    def get_messages(
        self,
        conversation_id: Union[int, str, uuid.UUID],
        limit: int = 100,
        offset: int = 0
    ) -> List[Message]:
        """
        Get messages for conversation.

        Args:
            conversation_id: Conversation ID or UUID
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List[Message]: List of messages
        """
        try:
            # Get conversation
            conversation = None

            if isinstance(conversation_id, (str, uuid.UUID)):
                conversation = self.get_by_conversation_id(conversation_id)
            else:
                conversation = self.get_by_id(conversation_id)

            if not conversation:
                return []

            # Get messages
            query = (
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.created_at)
                .limit(limit)
                .offset(offset)
            )

            result = self.session.execute(query)
            return list(result.scalars().all())
        except (SQLAlchemyError, ValueError) as e:
            logger.error(f"Error getting messages for conversation: {str(e)}")
            return []

    def get_messages_in_range(
        self,
        conversation_id: Union[int, str, uuid.UUID],
        start_id: int,
        end_id: int
    ) -> List[Message]:
        """
        Get messages in a specific ID range for a conversation.

        Args:
            conversation_id: Conversation ID or UUID
            start_id: Start message ID (inclusive)
            end_id: End message ID (inclusive)

        Returns:
            List[Message]: List of messages in the range
        """
        try:
            # Get conversation
            conversation = None

            if isinstance(conversation_id, (str, uuid.UUID)):
                conversation = self.get_by_conversation_id(conversation_id)
            else:
                conversation = self.get_by_id(conversation_id)

            if not conversation:
                return []

            # Get messages in range
            query = (
                select(Message)
                .where(
                    and_(
                        Message.conversation_id == conversation.id,
                        Message.id >= start_id,
                        Message.id <= end_id
                    )
                )
                .order_by(Message.id)
            )

            result = self.session.execute(query)
            return list(result.scalars().all())
        except (SQLAlchemyError, ValueError) as e:
            logger.error(f"Error getting messages in range: {str(e)}")
            return []

    def add_message_to_context(
        self,
        message_id: int,
        priority: ContextPriority = ContextPriority.MEDIUM
    ) -> Optional[ContextItem]:
        """
        Add a message to the context window.

        Args:
            message_id: Message ID
            priority: Priority level for the message in the context window

        Returns:
            Optional[ContextItem]: Created context item or None if error
        """
        try:
            # Get message
            message = self.session.get(Message, message_id)
            if not message:
                logger.error(f"Message not found: {message_id}")
                return None

            # Get or create context window
            window_repo = ContextWindowRepository(self.session)
            window = window_repo.get_active_window_for_conversation(message.conversation_id)
            if not window:
                logger.error(f"Failed to get or create context window for conversation {message.conversation_id}")
                return None

            # Add message to context
            item_repo = ContextItemRepository(self.session)
            context_item = item_repo.add_message_to_context(
                window_id=window.id,
                message_id=message_id,
                priority=priority
            )

            return context_item
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error adding message to context: {str(e)}")
            return None

    def get_conversation_context(
        self,
        conversation_id: Union[int, str, uuid.UUID],
        max_tokens: int = 4000,
        include_system_prompt: bool = True
    ) -> List[Dict]:
        """
        Get context for a conversation formatted for LLM input.

        Args:
            conversation_id: Conversation ID or UUID
            max_tokens: Maximum number of tokens to include
            include_system_prompt: Whether to include system prompt

        Returns:
            List[Dict]: List of context messages formatted for LLM input
        """
        try:
            # Get conversation
            conversation = None

            if isinstance(conversation_id, (str, uuid.UUID)):
                conversation = self.get_by_conversation_id(conversation_id)
            else:
                conversation = self.get_by_id(conversation_id)

            if not conversation:
                return []

            # Get context service
            from app.services.context_service import ContextService
            context_service = ContextService(self.session)

            # Get context
            context_messages = context_service.get_context_for_conversation(
                conversation_id=conversation.id,
                max_tokens=max_tokens,
                include_system_prompt=include_system_prompt
            )

            return context_messages
        except (SQLAlchemyError, ValueError) as e:
            logger.error(f"Error getting conversation context: {str(e)}")
            return []

    def delete_conversation(self, conversation_id: Union[str, uuid.UUID]) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: Conversation ID or UUID

        Returns:
            bool: True if the conversation was deleted, False if not found
        """
        try:
            # Get conversation
            conversation = None

            if isinstance(conversation_id, str):
                conversation = self.get_by_conversation_id(conversation_id)
            else:
                conversation = self.get_by_conversation_id(conversation_id)

            if not conversation:
                return False

            # Delete context windows and items first
            from app.models.context import ContextWindow, ContextItem

            # Get context windows
            window_query = select(ContextWindow).where(ContextWindow.conversation_id == conversation.id)
            window_result = self.session.execute(window_query)
            windows = list(window_result.scalars().all())

            for window in windows:
                # Delete context items
                item_query = select(ContextItem).where(ContextItem.context_window_id == window.id)
                item_result = self.session.execute(item_query)
                items = list(item_result.scalars().all())

                for item in items:
                    self.session.delete(item)

                # Delete window
                self.session.delete(window)

            # Delete messages (due to foreign key constraint)
            query = select(Message).where(Message.conversation_id == conversation.id)
            result = self.session.execute(query)
            messages = list(result.scalars().all())

            for message in messages:
                self.session.delete(message)

            # Delete conversation
            self.session.delete(conversation)
            self.session.commit()

            # Clear cache
            self._cache_delete(conversation.id)

            return True
        except (SQLAlchemyError, ValueError) as e:
            self.session.rollback()
            logger.error(f"Error deleting conversation: {str(e)}")
            return False
