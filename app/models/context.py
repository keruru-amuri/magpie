"""
Context management models for the MAGPIE platform.
"""
import enum
from typing import Dict, List, Optional, Union

from sqlalchemy import (
    Boolean, Column, Enum, ForeignKey, Integer,
    String, Text, UniqueConstraint, func, JSON, Float
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseModel
from app.models.conversation import Conversation, JSONBType, Message


class ContextPriority(str, enum.Enum):
    """
    Enum for context priority levels.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContextType(str, enum.Enum):
    """
    Enum for context types.
    """
    MESSAGE = "message"
    SUMMARY = "summary"
    USER_PREFERENCE = "user_preference"
    SYSTEM = "system"
    METADATA = "metadata"


class ContextWindow(BaseModel):
    """
    Context window model for tracking token usage and context boundaries.
    """
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversation.id"),
        nullable=False
    )
    max_tokens = Column(Integer, default=4000, nullable=False)
    current_tokens = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="context_windows"
    )
    context_items: Mapped[List["ContextItem"]] = relationship(
        "ContextItem", back_populates="context_window", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """
        String representation of the context window.

        Returns:
            str: Context window representation
        """
        return f"<ContextWindow {self.id} ({self.current_tokens}/{self.max_tokens})>"


class ContextItem(BaseModel):
    """
    Context item model for storing individual context elements.
    """
    id = Column(Integer, primary_key=True, index=True)
    context_window_id = Column(
        Integer,
        ForeignKey("contextwindow.id"),
        nullable=False
    )
    message_id = Column(
        Integer,
        ForeignKey("message.id"),
        nullable=True
    )
    content = Column(Text, nullable=True)
    context_type = Column(Enum(ContextType), nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    priority = Column(Enum(ContextPriority), default=ContextPriority.MEDIUM, nullable=False)
    relevance_score = Column(Float, default=1.0, nullable=False)
    position = Column(Integer, default=0, nullable=False)
    is_included = Column(Boolean, default=True, nullable=False)
    meta_data = Column(JSONBType, nullable=True)
    
    # Relationships
    context_window: Mapped["ContextWindow"] = relationship(
        "ContextWindow", back_populates="context_items"
    )
    message: Mapped["Message"] = relationship(
        "Message", back_populates="context_items"
    )
    
    def __repr__(self) -> str:
        """
        String representation of the context item.

        Returns:
            str: Context item representation
        """
        return f"<ContextItem {self.id} ({self.context_type})>"


class ContextTag(BaseModel):
    """
    Context tag model for metadata tagging of context items.
    """
    id = Column(Integer, primary_key=True, index=True)
    context_item_id = Column(
        Integer,
        ForeignKey("contextitem.id"),
        nullable=False
    )
    tag_key = Column(String(100), nullable=False)
    tag_value = Column(String(255), nullable=False)
    
    # Relationships
    context_item: Mapped["ContextItem"] = relationship(
        "ContextItem", backref="tags"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('context_item_id', 'tag_key', name='uix_context_tag'),
    )
    
    def __repr__(self) -> str:
        """
        String representation of the context tag.

        Returns:
            str: Context tag representation
        """
        return f"<ContextTag {self.id} ({self.tag_key}:{self.tag_value})>"


class ContextSummary(BaseModel):
    """
    Context summary model for storing summarized conversation segments.
    """
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversation.id"),
        nullable=False
    )
    start_message_id = Column(
        Integer,
        ForeignKey("message.id"),
        nullable=True
    )
    end_message_id = Column(
        Integer,
        ForeignKey("message.id"),
        nullable=True
    )
    summary_content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    meta_data = Column(JSONBType, nullable=True)
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", backref="summaries"
    )
    start_message: Mapped["Message"] = relationship(
        "Message", foreign_keys=[start_message_id]
    )
    end_message: Mapped["Message"] = relationship(
        "Message", foreign_keys=[end_message_id]
    )
    
    def __repr__(self) -> str:
        """
        String representation of the context summary.

        Returns:
            str: Context summary representation
        """
        return f"<ContextSummary {self.id}>"


class UserPreference(BaseModel):
    """
    User preference model for storing user preferences extracted from conversations.
    """
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("user.id"),
        nullable=False
    )
    preference_key = Column(String(100), nullable=False)
    preference_value = Column(String(255), nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    source_message_id = Column(
        Integer,
        ForeignKey("message.id"),
        nullable=True
    )
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User", backref="preferences"
    )
    source_message: Mapped["Message"] = relationship(
        "Message", backref="extracted_preferences"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'preference_key', name='uix_user_preference'),
    )
    
    def __repr__(self) -> str:
        """
        String representation of the user preference.

        Returns:
            str: User preference representation
        """
        return f"<UserPreference {self.id} ({self.preference_key}:{self.preference_value})>"
