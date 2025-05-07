"""
Context repository for the MAGPIE platform.
"""
import logging
from typing import Dict, List, Optional, Union, Tuple

from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.models.context import (
    ContextWindow, ContextItem, ContextTag, ContextSummary,
    ContextType, ContextPriority, UserPreference
)
from app.models.conversation import Conversation, Message
from app.repositories.base import BaseRepository
from app.services.token_utils import count_tokens_approximate

# Configure logging
logger = logging.getLogger(__name__)


class ContextWindowRepository(BaseRepository[ContextWindow]):
    """
    Repository for ContextWindow model.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(ContextWindow, session)

    def get_active_window_for_conversation(
        self,
        conversation_id: Union[int, str]
    ) -> Optional[ContextWindow]:
        """
        Get active context window for a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Optional[ContextWindow]: Active context window or None if not found
        """
        try:
            # Get conversation
            conversation = None
            if isinstance(conversation_id, str):
                # Get conversation by UUID
                from app.repositories.conversation import ConversationRepository
                conversation_repo = ConversationRepository(self.session)
                conversation = conversation_repo.get_by_conversation_id(conversation_id)
            else:
                # Get conversation by ID
                conversation = self.session.get(Conversation, conversation_id)

            if not conversation:
                return None

            # Get active context window
            query = (
                select(ContextWindow)
                .where(
                    and_(
                        ContextWindow.conversation_id == conversation.id,
                        ContextWindow.is_active == True
                    )
                )
                .options(joinedload(ContextWindow.context_items))
            )

            result = self.session.execute(query)
            window = result.scalar_one_or_none()

            # Create new window if not found
            if not window:
                window = ContextWindow(
                    conversation_id=conversation.id,
                    max_tokens=4000,  # Default max tokens
                    current_tokens=0,
                    is_active=True
                )
                self.session.add(window)
                self.session.flush()

            return window
        except SQLAlchemyError as e:
            logger.error(f"Error getting active context window: {str(e)}")
            return None

    def update_token_count(
        self,
        window_id: int,
        token_count: int
    ) -> Optional[ContextWindow]:
        """
        Update token count for a context window.

        Args:
            window_id: Context window ID
            token_count: New token count

        Returns:
            Optional[ContextWindow]: Updated context window or None if error
        """
        try:
            window = self.get_by_id(window_id)
            if not window:
                return None

            window.current_tokens = token_count
            self.session.flush()

            return window
        except SQLAlchemyError as e:
            logger.error(f"Error updating token count: {str(e)}")
            return None


class ContextItemRepository(BaseRepository[ContextItem]):
    """
    Repository for ContextItem model.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(ContextItem, session)

    def get_items_for_window(
        self,
        window_id: int,
        included_only: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[ContextItem]:
        """
        Get context items for a window.

        Args:
            window_id: Context window ID
            included_only: Whether to return only included items
            limit: Maximum number of items to return
            offset: Number of items to skip

        Returns:
            List[ContextItem]: List of context items
        """
        try:
            query = select(ContextItem).where(ContextItem.context_window_id == window_id)

            if included_only:
                query = query.where(ContextItem.is_included == True)

            # Order by position and then by creation time
            query = query.order_by(ContextItem.position, ContextItem.created_at)

            # Apply pagination
            if limit > 0:
                query = query.limit(limit).offset(offset)

            result = self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting context items: {str(e)}")
            return []

    def add_message_to_context(
        self,
        window_id: int,
        message_id: int,
        priority: ContextPriority = ContextPriority.MEDIUM,
        position: Optional[int] = None
    ) -> Optional[ContextItem]:
        """
        Add a message to the context window.

        Args:
            window_id: Context window ID
            message_id: Message ID
            priority: Priority level
            position: Position in the context window (if None, appends to the end)

        Returns:
            Optional[ContextItem]: Created context item or None if error
        """
        try:
            # Get message
            message = self.session.get(Message, message_id)
            if not message:
                return None

            # Calculate token count
            token_count = count_tokens_approximate(message.content)

            # Get position if not provided
            if position is None:
                # Get highest position and add 1
                query = (
                    select(func.max(ContextItem.position))
                    .where(ContextItem.context_window_id == window_id)
                )
                result = self.session.execute(query)
                max_position = result.scalar_one_or_none() or 0
                position = max_position + 1

            # Create context item
            context_item = ContextItem(
                context_window_id=window_id,
                message_id=message_id,
                content=None,  # Content is stored in the message
                context_type=ContextType.MESSAGE,
                token_count=token_count,
                priority=priority,
                relevance_score=1.0,
                position=position,
                is_included=True
            )

            # Add to session and flush to get ID
            self.session.add(context_item)
            self.session.flush()

            # Update window token count
            window_repo = ContextWindowRepository(self.session)
            window = window_repo.get_by_id(window_id)
            if window:
                window.current_tokens += token_count
                self.session.flush()

            return context_item
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error adding message to context: {str(e)}")
            return None

    def add_content_to_context(
        self,
        window_id: int,
        content: str,
        context_type: ContextType,
        priority: ContextPriority = ContextPriority.MEDIUM,
        position: Optional[int] = None,
        meta_data: Optional[Dict] = None
    ) -> Optional[ContextItem]:
        """
        Add content to the context window.

        Args:
            window_id: Context window ID
            content: Content text
            context_type: Context type
            priority: Priority level
            position: Position in the context window (if None, appends to the end)
            meta_data: Optional metadata

        Returns:
            Optional[ContextItem]: Created context item or None if error
        """
        try:
            # Calculate token count
            token_count = count_tokens_approximate(content)

            # Get position if not provided
            if position is None:
                # Get highest position and add 1
                query = (
                    select(func.max(ContextItem.position))
                    .where(ContextItem.context_window_id == window_id)
                )
                result = self.session.execute(query)
                max_position = result.scalar_one_or_none() or 0
                position = max_position + 1

            # Create context item
            context_item = ContextItem(
                context_window_id=window_id,
                message_id=None,
                content=content,
                context_type=context_type,
                token_count=token_count,
                priority=priority,
                relevance_score=1.0,
                position=position,
                is_included=True,
                meta_data=meta_data
            )

            # Add to session and flush to get ID
            self.session.add(context_item)
            self.session.flush()

            # Update window token count
            window_repo = ContextWindowRepository(self.session)
            window = window_repo.get_by_id(window_id)
            if window:
                window.current_tokens += token_count
                self.session.flush()

            return context_item
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error adding content to context: {str(e)}")
            return None

    def update_item_inclusion(
        self,
        item_id: int,
        is_included: bool
    ) -> Optional[ContextItem]:
        """
        Update inclusion status of a context item.

        Args:
            item_id: Context item ID
            is_included: Whether the item should be included

        Returns:
            Optional[ContextItem]: Updated context item or None if error
        """
        try:
            item = self.get_by_id(item_id)
            if not item:
                return None

            # Update window token count if inclusion status changed
            if item.is_included != is_included:
                window_repo = ContextWindowRepository(self.session)
                window = window_repo.get_by_id(item.context_window_id)
                if window:
                    if is_included:
                        window.current_tokens += item.token_count
                    else:
                        window.current_tokens -= item.token_count
                    self.session.flush()

            # Update inclusion status
            item.is_included = is_included
            self.session.flush()

            return item
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating item inclusion: {str(e)}")
            return None

    def update_item_priority(
        self,
        item_id: int,
        priority: ContextPriority
    ) -> Optional[ContextItem]:
        """
        Update priority of a context item.

        Args:
            item_id: Context item ID
            priority: New priority

        Returns:
            Optional[ContextItem]: Updated context item or None if error
        """
        try:
            item = self.get_by_id(item_id)
            if not item:
                return None

            item.priority = priority
            self.session.flush()

            return item
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating item priority: {str(e)}")
            return None

    def update_item_relevance(
        self,
        item_id: int,
        relevance_score: float
    ) -> Optional[ContextItem]:
        """
        Update relevance score of a context item.

        Args:
            item_id: Context item ID
            relevance_score: New relevance score

        Returns:
            Optional[ContextItem]: Updated context item or None if error
        """
        try:
            item = self.get_by_id(item_id)
            if not item:
                return None

            item.relevance_score = relevance_score
            self.session.flush()

            return item
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating item relevance: {str(e)}")
            return None


class ContextTagRepository(BaseRepository[ContextTag]):
    """
    Repository for ContextTag model.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(ContextTag, session)

    def get_tags_for_item(self, item_id: int) -> List[ContextTag]:
        """
        Get tags for a context item.

        Args:
            item_id: Context item ID

        Returns:
            List[ContextTag]: List of tags
        """
        try:
            query = select(ContextTag).where(ContextTag.context_item_id == item_id)
            result = self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting tags: {str(e)}")
            return []

    def add_tag(
        self,
        item_id: int,
        key: str,
        value: str
    ) -> Optional[ContextTag]:
        """
        Add a tag to a context item.

        Args:
            item_id: Context item ID
            key: Tag key
            value: Tag value

        Returns:
            Optional[ContextTag]: Created tag or None if error
        """
        try:
            # Check if tag already exists
            query = select(ContextTag).where(
                and_(
                    ContextTag.context_item_id == item_id,
                    ContextTag.tag_key == key
                )
            )
            result = self.session.execute(query)
            existing_tag = result.scalar_one_or_none()

            if existing_tag:
                # Update existing tag
                existing_tag.tag_value = value
                self.session.flush()
                return existing_tag
            else:
                # Create new tag
                tag = ContextTag(
                    context_item_id=item_id,
                    tag_key=key,
                    tag_value=value
                )
                self.session.add(tag)
                self.session.flush()
                return tag
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error adding tag: {str(e)}")
            return None


class ContextSummaryRepository(BaseRepository[ContextSummary]):
    """
    Repository for ContextSummary model.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(ContextSummary, session)

    def get_summaries_for_conversation(
        self,
        conversation_id: int,
        active_only: bool = True
    ) -> List[ContextSummary]:
        """
        Get summaries for a conversation.

        Args:
            conversation_id: Conversation ID
            active_only: Whether to return only active summaries

        Returns:
            List[ContextSummary]: List of summaries
        """
        try:
            query = select(ContextSummary).where(
                ContextSummary.conversation_id == conversation_id
            )

            if active_only:
                query = query.where(ContextSummary.is_active == True)

            # Order by creation time
            query = query.order_by(ContextSummary.created_at)

            result = self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting summaries: {str(e)}")
            return []

    def create_summary(
        self,
        conversation_id: int,
        summary_content: str,
        start_message_id: Optional[int] = None,
        end_message_id: Optional[int] = None,
        meta_data: Optional[Dict] = None
    ) -> Optional[ContextSummary]:
        """
        Create a summary for a conversation.

        Args:
            conversation_id: Conversation ID
            summary_content: Summary content
            start_message_id: Start message ID
            end_message_id: End message ID
            meta_data: Optional metadata

        Returns:
            Optional[ContextSummary]: Created summary or None if error
        """
        try:
            # Calculate token count
            token_count = count_tokens_approximate(summary_content)

            # Create summary
            summary = ContextSummary(
                conversation_id=conversation_id,
                start_message_id=start_message_id,
                end_message_id=end_message_id,
                summary_content=summary_content,
                token_count=token_count,
                is_active=True,
                meta_data=meta_data
            )

            # Add to session and flush to get ID
            self.session.add(summary)
            self.session.flush()

            return summary
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error creating summary: {str(e)}")
            return None

    def add_summary_to_context(
        self,
        summary_id: int,
        window_id: int,
        priority: ContextPriority = ContextPriority.HIGH,
        position: Optional[int] = None
    ) -> Optional[Tuple[ContextSummary, ContextItem]]:
        """
        Add a summary to a context window.

        Args:
            summary_id: Summary ID
            window_id: Context window ID
            priority: Priority level
            position: Position in the context window (if None, appends to the end)

        Returns:
            Optional[Tuple[ContextSummary, ContextItem]]: Tuple of summary and context item or None if error
        """
        try:
            # Get summary
            summary = self.get_by_id(summary_id)
            if not summary:
                return None

            # Add to context
            item_repo = ContextItemRepository(self.session)
            context_item = item_repo.add_content_to_context(
                window_id=window_id,
                content=summary.summary_content,
                context_type=ContextType.SUMMARY,
                priority=priority,
                position=position,
                meta_data={
                    "summary_id": summary.id,
                    "start_message_id": summary.start_message_id,
                    "end_message_id": summary.end_message_id
                }
            )

            if not context_item:
                return None

            return (summary, context_item)
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error adding summary to context: {str(e)}")
            return None


class UserPreferenceRepository(BaseRepository[UserPreference]):
    """
    Repository for UserPreference model.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(UserPreference, session)

    def get_preferences_for_user(self, user_id: int) -> List[UserPreference]:
        """
        Get preferences for a user.

        Args:
            user_id: User ID

        Returns:
            List[UserPreference]: List of preferences
        """
        try:
            query = (
                select(UserPreference)
                .where(
                    and_(
                        UserPreference.user_id == user_id,
                        UserPreference.is_active == True
                    )
                )
                .order_by(UserPreference.preference_key)
            )
            result = self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting preferences: {str(e)}")
            return []

    def get_preference(
        self,
        user_id: int,
        key: str
    ) -> Optional[UserPreference]:
        """
        Get a specific preference for a user.

        Args:
            user_id: User ID
            key: Preference key

        Returns:
            Optional[UserPreference]: Preference or None if not found
        """
        try:
            query = select(UserPreference).where(
                and_(
                    UserPreference.user_id == user_id,
                    UserPreference.preference_key == key,
                    UserPreference.is_active == True
                )
            )
            result = self.session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting preference: {str(e)}")
            return None

    def set_preference(
        self,
        user_id: int,
        key: str,
        value: str,
        confidence: float = 1.0,
        source_message_id: Optional[int] = None
    ) -> Optional[UserPreference]:
        """
        Set a preference for a user.

        Args:
            user_id: User ID
            key: Preference key
            value: Preference value
            confidence: Confidence level
            source_message_id: Source message ID

        Returns:
            Optional[UserPreference]: Created or updated preference or None if error
        """
        try:
            # Check if preference already exists
            existing_pref = self.get_preference(user_id, key)

            if existing_pref:
                # Update existing preference
                existing_pref.preference_value = value
                existing_pref.confidence = confidence
                existing_pref.source_message_id = source_message_id or existing_pref.source_message_id
                self.session.flush()
                return existing_pref
            else:
                # Create new preference
                preference = UserPreference(
                    user_id=user_id,
                    preference_key=key,
                    preference_value=value,
                    confidence=confidence,
                    source_message_id=source_message_id,
                    is_active=True
                )
                self.session.add(preference)
                self.session.flush()
                return preference
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error setting preference: {str(e)}")
            return None

    def add_preferences_to_context(
        self,
        user_id: int,
        window_id: int,
        priority: ContextPriority = ContextPriority.HIGH,
        position: Optional[int] = None,
        keys: Optional[List[str]] = None
    ) -> List[ContextItem]:
        """
        Add user preferences to a context window.

        Args:
            user_id: User ID
            window_id: Context window ID
            priority: Priority level
            position: Position in the context window (if None, appends to the end)
            keys: Optional list of preference keys to include (if None, includes all)

        Returns:
            List[ContextItem]: List of created context items
        """
        try:
            # Get preferences
            preferences = self.get_preferences_for_user(user_id)
            if not preferences:
                return []

            # Filter by keys if provided
            if keys:
                preferences = [p for p in preferences if p.preference_key in keys]

            # Add to context
            item_repo = ContextItemRepository(self.session)
            context_items = []

            for i, pref in enumerate(preferences):
                # Format preference as content
                content = f"User preference: {pref.preference_key} = {pref.preference_value}"

                # Calculate position if provided
                pos = None
                if position is not None:
                    pos = position + i

                # Add to context
                context_item = item_repo.add_content_to_context(
                    window_id=window_id,
                    content=content,
                    context_type=ContextType.USER_PREFERENCE,
                    priority=priority,
                    position=pos,
                    meta_data={
                        "preference_id": pref.id,
                        "preference_key": pref.preference_key,
                        "preference_value": pref.preference_value,
                        "confidence": pref.confidence
                    }
                )

                if context_item:
                    context_items.append(context_item)

            return context_items
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error adding preferences to context: {str(e)}")
            return []
