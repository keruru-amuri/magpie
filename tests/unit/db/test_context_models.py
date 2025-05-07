"""
Unit tests for context management models.
"""
import pytest
import uuid
from datetime import datetime

from app.models.base import BaseModel
from app.models.user import User, UserRole
from app.models.conversation import Conversation, Message, MessageRole, AgentType
from app.models.context import (
    ContextWindow, ContextItem, ContextTag, ContextSummary,
    ContextType, ContextPriority, UserPreference
)


class TestContextModels:
    """
    Test context management models.
    """
    
    def test_create_context_window(self):
        """
        Test creating a context window.
        """
        # Create context window
        window = ContextWindow(
            conversation_id=1,
            max_tokens=4000,
            current_tokens=0,
            is_active=True
        )
        
        # Verify window
        assert window.conversation_id == 1
        assert window.max_tokens == 4000
        assert window.current_tokens == 0
        assert window.is_active is True
    
    def test_create_context_item(self):
        """
        Test creating a context item.
        """
        # Create context item
        item = ContextItem(
            context_window_id=1,
            message_id=1,
            content=None,
            context_type=ContextType.MESSAGE,
            token_count=10,
            priority=ContextPriority.MEDIUM,
            relevance_score=1.0,
            position=0,
            is_included=True
        )
        
        # Verify item
        assert item.context_window_id == 1
        assert item.message_id == 1
        assert item.content is None
        assert item.context_type == ContextType.MESSAGE
        assert item.token_count == 10
        assert item.priority == ContextPriority.MEDIUM
        assert item.relevance_score == 1.0
        assert item.position == 0
        assert item.is_included is True
    
    def test_create_context_item_with_content(self):
        """
        Test creating a context item with content.
        """
        # Create context item
        item = ContextItem(
            context_window_id=1,
            message_id=None,
            content="Test content",
            context_type=ContextType.SYSTEM,
            token_count=2,
            priority=ContextPriority.HIGH,
            relevance_score=1.0,
            position=0,
            is_included=True
        )
        
        # Verify item
        assert item.context_window_id == 1
        assert item.message_id is None
        assert item.content == "Test content"
        assert item.context_type == ContextType.SYSTEM
        assert item.token_count == 2
        assert item.priority == ContextPriority.HIGH
        assert item.relevance_score == 1.0
        assert item.position == 0
        assert item.is_included is True
    
    def test_create_context_tag(self):
        """
        Test creating a context tag.
        """
        # Create context tag
        tag = ContextTag(
            context_item_id=1,
            tag_key="topic",
            tag_value="maintenance"
        )
        
        # Verify tag
        assert tag.context_item_id == 1
        assert tag.tag_key == "topic"
        assert tag.tag_value == "maintenance"
    
    def test_create_context_summary(self):
        """
        Test creating a context summary.
        """
        # Create context summary
        summary = ContextSummary(
            conversation_id=1,
            start_message_id=1,
            end_message_id=5,
            summary_content="This is a summary of the conversation",
            token_count=8,
            is_active=True
        )
        
        # Verify summary
        assert summary.conversation_id == 1
        assert summary.start_message_id == 1
        assert summary.end_message_id == 5
        assert summary.summary_content == "This is a summary of the conversation"
        assert summary.token_count == 8
        assert summary.is_active is True
    
    def test_create_user_preference(self):
        """
        Test creating a user preference.
        """
        # Create user preference
        preference = UserPreference(
            user_id=1,
            preference_key="preferred_format",
            preference_value="detailed",
            confidence=0.9,
            source_message_id=1,
            is_active=True
        )
        
        # Verify preference
        assert preference.user_id == 1
        assert preference.preference_key == "preferred_format"
        assert preference.preference_value == "detailed"
        assert preference.confidence == 0.9
        assert preference.source_message_id == 1
        assert preference.is_active is True
    
    def test_context_priority_enum(self):
        """
        Test context priority enum.
        """
        assert ContextPriority.LOW == "low"
        assert ContextPriority.MEDIUM == "medium"
        assert ContextPriority.HIGH == "high"
        assert ContextPriority.CRITICAL == "critical"
    
    def test_context_type_enum(self):
        """
        Test context type enum.
        """
        assert ContextType.MESSAGE == "message"
        assert ContextType.SUMMARY == "summary"
        assert ContextType.USER_PREFERENCE == "user_preference"
        assert ContextType.SYSTEM == "system"
        assert ContextType.METADATA == "metadata"
