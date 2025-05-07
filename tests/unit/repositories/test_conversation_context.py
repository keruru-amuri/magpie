"""
Unit tests for conversation context management.
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.models.conversation import Conversation, Message, MessageRole, AgentType
from app.models.context import (
    ContextWindow, ContextItem, ContextType, ContextPriority
)
from app.repositories.conversation import ConversationRepository
from app.repositories.context import (
    ContextWindowRepository, ContextItemRepository
)


class TestConversationContext:
    """
    Test conversation context management.
    """
    
    @pytest.fixture
    def mock_session(self):
        """
        Create a mock session.
        """
        session = MagicMock(spec=Session)
        return session
    
    @pytest.fixture
    def conversation_repo(self, mock_session):
        """
        Create a conversation repository with a mock session.
        """
        return ConversationRepository(mock_session)
    
    @pytest.fixture
    def context_window_repo(self, mock_session):
        """
        Create a context window repository with a mock session.
        """
        return ContextWindowRepository(mock_session)
    
    @pytest.fixture
    def context_item_repo(self, mock_session):
        """
        Create a context item repository with a mock session.
        """
        return ContextItemRepository(mock_session)
    
    @pytest.fixture
    def mock_conversation(self):
        """
        Create a mock conversation.
        """
        return Conversation(
            id=1,
            conversation_id=uuid.uuid4(),
            title="Test Conversation",
            user_id=1,
            agent_type=AgentType.DOCUMENTATION,
            is_active=True
        )
    
    @pytest.fixture
    def mock_message(self, mock_conversation):
        """
        Create a mock message.
        """
        return Message(
            id=1,
            conversation_id=mock_conversation.id,
            role=MessageRole.USER,
            content="Test message"
        )
    
    @pytest.fixture
    def mock_context_window(self, mock_conversation):
        """
        Create a mock context window.
        """
        return ContextWindow(
            id=1,
            conversation_id=mock_conversation.id,
            max_tokens=4000,
            current_tokens=0,
            is_active=True
        )
    
    @pytest.fixture
    def mock_context_item(self, mock_context_window, mock_message):
        """
        Create a mock context item.
        """
        return ContextItem(
            id=1,
            context_window_id=mock_context_window.id,
            message_id=mock_message.id,
            content=None,
            context_type=ContextType.MESSAGE,
            token_count=10,
            priority=ContextPriority.MEDIUM,
            relevance_score=1.0,
            position=0,
            is_included=True
        )
    
    def test_add_message_with_context(self, conversation_repo, mock_conversation, mock_session):
        """
        Test adding a message with context.
        """
        # Mock get_by_id to return the conversation
        mock_session.get.return_value = mock_conversation
        
        # Mock add_message_to_context
        with patch.object(ConversationRepository, 'add_message_to_context') as mock_add_to_context:
            # Call add_message with add_to_context=True
            message = Message(
                id=1,
                conversation_id=mock_conversation.id,
                role=MessageRole.USER,
                content="Test message"
            )
            mock_session.add.return_value = None
            mock_session.flush.return_value = None
            
            # Mock the created message
            conversation_repo.add_message = MagicMock(return_value=message)
            
            # Call add_message
            result = conversation_repo.add_message(
                conversation_id=mock_conversation.id,
                role=MessageRole.USER,
                content="Test message",
                add_to_context=True,
                context_priority=ContextPriority.HIGH
            )
            
            # Verify add_message_to_context was called
            mock_add_to_context.assert_called_once_with(message.id, ContextPriority.HIGH)
    
    def test_add_message_to_context(self, conversation_repo, mock_message, mock_session, mock_context_window):
        """
        Test adding a message to context.
        """
        # Mock get to return the message
        mock_session.get.return_value = mock_message
        
        # Mock ContextWindowRepository.get_active_window_for_conversation
        with patch.object(ContextWindowRepository, 'get_active_window_for_conversation') as mock_get_window:
            mock_get_window.return_value = mock_context_window
            
            # Mock ContextItemRepository.add_message_to_context
            with patch.object(ContextItemRepository, 'add_message_to_context') as mock_add_message:
                mock_context_item = ContextItem(
                    id=1,
                    context_window_id=mock_context_window.id,
                    message_id=mock_message.id,
                    content=None,
                    context_type=ContextType.MESSAGE,
                    token_count=10,
                    priority=ContextPriority.HIGH,
                    relevance_score=1.0,
                    position=0,
                    is_included=True
                )
                mock_add_message.return_value = mock_context_item
                
                # Call add_message_to_context
                result = conversation_repo.add_message_to_context(
                    message_id=mock_message.id,
                    priority=ContextPriority.HIGH
                )
                
                # Verify result
                assert result is not None
                assert result.message_id == mock_message.id
                assert result.priority == ContextPriority.HIGH
                
                # Verify ContextWindowRepository.get_active_window_for_conversation was called
                mock_get_window.assert_called_once_with(mock_message.conversation_id)
                
                # Verify ContextItemRepository.add_message_to_context was called
                mock_add_message.assert_called_once_with(
                    window_id=mock_context_window.id,
                    message_id=mock_message.id,
                    priority=ContextPriority.HIGH
                )
    
    def test_get_conversation_context(self, conversation_repo, mock_conversation, mock_session):
        """
        Test getting conversation context.
        """
        # Mock get_by_id to return the conversation
        mock_session.get.return_value = mock_conversation
        
        # Mock ContextService.get_context_for_conversation
        with patch('app.services.context_service.ContextService.get_context_for_conversation') as mock_get_context:
            mock_context = [
                {"role": "system", "content": "System prompt"},
                {"role": "user", "content": "User message"},
                {"role": "assistant", "content": "Assistant response"}
            ]
            mock_get_context.return_value = mock_context
            
            # Call get_conversation_context
            result = conversation_repo.get_conversation_context(
                conversation_id=mock_conversation.id,
                max_tokens=4000,
                include_system_prompt=True
            )
            
            # Verify result
            assert result == mock_context
            
            # Verify ContextService.get_context_for_conversation was called
            mock_get_context.assert_called_once_with(
                conversation_id=mock_conversation.id,
                max_tokens=4000,
                include_system_prompt=True
            )
    
    def test_get_messages_in_range(self, conversation_repo, mock_conversation, mock_session):
        """
        Test getting messages in a range.
        """
        # Mock get_by_id to return the conversation
        mock_session.get.return_value = mock_conversation
        
        # Mock session.execute
        mock_result = MagicMock()
        mock_messages = [
            Message(id=1, conversation_id=mock_conversation.id, role=MessageRole.USER, content="Message 1"),
            Message(id=2, conversation_id=mock_conversation.id, role=MessageRole.ASSISTANT, content="Message 2"),
            Message(id=3, conversation_id=mock_conversation.id, role=MessageRole.USER, content="Message 3")
        ]
        mock_result.scalars.return_value.all.return_value = mock_messages
        mock_session.execute.return_value = mock_result
        
        # Call get_messages_in_range
        result = conversation_repo.get_messages_in_range(
            conversation_id=mock_conversation.id,
            start_id=1,
            end_id=3
        )
        
        # Verify result
        assert result == mock_messages
        
        # Verify session.execute was called
        mock_session.execute.assert_called_once()
    
    def test_delete_conversation_with_context(self, conversation_repo, mock_conversation, mock_session):
        """
        Test deleting a conversation with context.
        """
        # Mock get_by_conversation_id to return the conversation
        conversation_repo.get_by_conversation_id = MagicMock(return_value=mock_conversation)
        
        # Mock session.execute for context windows
        mock_window_result = MagicMock()
        mock_windows = [
            ContextWindow(id=1, conversation_id=mock_conversation.id, max_tokens=4000, current_tokens=0, is_active=True)
        ]
        mock_window_result.scalars.return_value.all.return_value = mock_windows
        
        # Mock session.execute for context items
        mock_item_result = MagicMock()
        mock_items = [
            ContextItem(id=1, context_window_id=1, message_id=1, content=None, context_type=ContextType.MESSAGE)
        ]
        mock_item_result.scalars.return_value.all.return_value = mock_items
        
        # Mock session.execute for messages
        mock_message_result = MagicMock()
        mock_messages = [
            Message(id=1, conversation_id=mock_conversation.id, role=MessageRole.USER, content="Message 1")
        ]
        mock_message_result.scalars.return_value.all.return_value = mock_messages
        
        # Set up mock_session.execute to return different results based on the query
        def mock_execute_side_effect(query):
            if "ContextWindow" in str(query):
                return mock_window_result
            elif "ContextItem" in str(query):
                return mock_item_result
            else:
                return mock_message_result
        
        mock_session.execute.side_effect = mock_execute_side_effect
        
        # Call delete_conversation
        result = conversation_repo.delete_conversation(
            conversation_id=mock_conversation.conversation_id
        )
        
        # Verify result
        assert result is True
        
        # Verify session.delete was called for all objects
        assert mock_session.delete.call_count == 1 + len(mock_items) + len(mock_windows) + len(mock_messages)
        
        # Verify session.commit was called
        mock_session.commit.assert_called_once()
