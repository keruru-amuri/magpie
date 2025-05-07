"""
Conversation model for the MAGPIE platform.
"""
import enum
import json
import uuid
from typing import List, Optional, ForwardRef

from sqlalchemy import (
    Boolean, Column, Enum, ForeignKey, Integer,
    String, Text, UniqueConstraint, func, JSON
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.types import TypeDecorator

from app.core.db.connection import TESTING
from app.models.base import BaseModel

# Forward references for type hints
ContextWindowRef = ForwardRef("ContextWindow")
ContextItemRef = ForwardRef("ContextItem")


class JSONBType(TypeDecorator):
    """
    Platform-independent JSONB type.
    Uses JSONB for PostgreSQL and JSON for SQLite.
    """

    impl = JSON

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import JSONB
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


class AgentType(str, enum.Enum):
    """
    Enum for agent types.
    """

    DOCUMENTATION = "documentation"
    TROUBLESHOOTING = "troubleshooting"
    MAINTENANCE = "maintenance"


class Conversation(BaseModel):
    """
    Conversation model for storing conversation history.
    """

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )
    title = Column(String(255), nullable=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    agent_type = Column(Enum(AgentType), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    meta_data = Column(JSONBType, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )
    context_windows: Mapped[List["ContextWindow"]] = relationship(
        "ContextWindow", back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """
        String representation of the conversation.

        Returns:
            str: Conversation representation
        """
        return f"<Conversation {self.conversation_id} ({self.agent_type})>"


class MessageRole(str, enum.Enum):
    """
    Enum for message roles.
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class Message(BaseModel):
    """
    Message model for storing conversation messages.
    """

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversation.id"),
        nullable=False
    )
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    meta_data = Column(JSONBType, nullable=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )
    context_items: Mapped[List["ContextItem"]] = relationship(
        "ContextItem", back_populates="message"
    )

    def __repr__(self) -> str:
        """
        String representation of the message.

        Returns:
            str: Message representation
        """
        return f"<Message {self.id} ({self.role})>"
