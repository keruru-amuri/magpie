"""
WebSocket schemas for MAGPIE platform.

This module provides schemas for WebSocket messages.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field

from app.models.conversation import AgentType


class MessageType(str, Enum):
    """WebSocket message types."""
    
    # Chat messages
    MESSAGE = "message"
    TYPING = "typing"
    
    # Connection events
    CONNECTION = "connection"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    
    # Agent events
    AGENT_CHANGE = "agent_change"
    
    # Feedback
    FEEDBACK = "feedback"
    FEEDBACK_RECEIVED = "feedback_received"
    
    # Errors
    ERROR = "error"


class ConnectionStatus(str, Enum):
    """WebSocket connection status."""
    
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"


class WebSocketMessage(BaseModel):
    """Base WebSocket message."""
    
    type: MessageType
    payload: Dict[str, Any]


class ChatMessage(BaseModel):
    """Chat message model."""
    
    id: str
    content: str
    role: str
    timestamp: datetime
    agent_type: Optional[AgentType] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class MessageEvent(WebSocketMessage):
    """Message event."""
    
    type: MessageType = MessageType.MESSAGE
    payload: Dict[str, Any] = Field(...)
    
    class Config:
        schema_extra = {
            "example": {
                "type": "message",
                "payload": {
                    "message": {
                        "id": "msg-123",
                        "content": "Hello, how can I help you?",
                        "role": "assistant",
                        "timestamp": "2023-01-01T00:00:00Z",
                        "agent_type": "documentation",
                        "confidence": 0.95
                    },
                    "conversation_id": "conv-123"
                }
            }
        }


class TypingEvent(WebSocketMessage):
    """Typing indicator event."""
    
    type: MessageType = MessageType.TYPING
    payload: Dict[str, Any] = Field(...)
    
    class Config:
        schema_extra = {
            "example": {
                "type": "typing",
                "payload": {
                    "is_typing": True,
                    "conversation_id": "conv-123",
                    "agent_type": "documentation"
                }
            }
        }


class AgentChangeEvent(WebSocketMessage):
    """Agent change event."""
    
    type: MessageType = MessageType.AGENT_CHANGE
    payload: Dict[str, Any] = Field(...)
    
    class Config:
        schema_extra = {
            "example": {
                "type": "agent_change",
                "payload": {
                    "from_agent": "documentation",
                    "to_agent": "troubleshooting",
                    "reason": "Query requires troubleshooting expertise",
                    "conversation_id": "conv-123"
                }
            }
        }


class ConnectionEvent(WebSocketMessage):
    """Connection event."""
    
    type: MessageType = MessageType.CONNECTION
    payload: Dict[str, Any] = Field(...)
    
    class Config:
        schema_extra = {
            "example": {
                "type": "connection",
                "payload": {
                    "status": "connected",
                    "user_id": "user-123",
                    "timestamp": "2023-01-01T00:00:00Z"
                }
            }
        }


class ErrorEvent(WebSocketMessage):
    """Error event."""
    
    type: MessageType = MessageType.ERROR
    payload: Dict[str, Any] = Field(...)
    
    class Config:
        schema_extra = {
            "example": {
                "type": "error",
                "payload": {
                    "error": {
                        "code": "invalid_message",
                        "message": "Invalid message format"
                    },
                    "conversation_id": "conv-123"
                }
            }
        }


class FeedbackEvent(WebSocketMessage):
    """Feedback event."""
    
    type: MessageType = MessageType.FEEDBACK
    payload: Dict[str, Any] = Field(...)
    
    class Config:
        schema_extra = {
            "example": {
                "type": "feedback",
                "payload": {
                    "message_id": "msg-123",
                    "feedback": "positive",
                    "comments": "This was very helpful!"
                }
            }
        }


class FeedbackReceivedEvent(WebSocketMessage):
    """Feedback received event."""
    
    type: MessageType = MessageType.FEEDBACK_RECEIVED
    payload: Dict[str, Any] = Field(...)
    
    class Config:
        schema_extra = {
            "example": {
                "type": "feedback_received",
                "payload": {
                    "message_id": "msg-123",
                    "status": "success"
                }
            }
        }
