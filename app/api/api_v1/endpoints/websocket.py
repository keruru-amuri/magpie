"""
WebSocket endpoints for MAGPIE platform.

This module provides WebSocket endpoints for real-time communication.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError

from app.api.deps import get_current_user_from_token
from app.core.logging import get_logger
from app.core.websocket import connection_manager
from app.models.conversation import AgentType
from app.models.user import User
from app.schemas.websocket import (
    MessageType,
    WebSocketMessage,
    ChatMessage,
    MessageEvent,
    TypingEvent,
    AgentChangeEvent,
    ConnectionEvent,
    ErrorEvent,
)

# Import mock data service for testing
from app.core.mock.service import mock_data_service

# Configure logger
logger = get_logger(__name__)

# Create router
router = APIRouter()


async def get_user_from_token(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
) -> Optional[User]:
    """
    Get user from token for WebSocket authentication.

    Args:
        websocket: WebSocket connection
        token: JWT token

    Returns:
        Optional[User]: User if authenticated, None otherwise
    """
    if not token:
        return None

    try:
        # Use the same function as for HTTP authentication
        user = await get_current_user_from_token(token)
        return user
    except HTTPException:
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(...),
    conversation_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for real-time communication.

    Args:
        websocket: WebSocket connection
        user_id: User ID
        conversation_id: Optional conversation ID
        token: Optional JWT token for authentication
    """
    # Authenticate user if token is provided
    user = None
    if token:
        user = await get_user_from_token(websocket, token)
        if not user:
            # Authentication failed
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Use authenticated user ID
        user_id = str(user.id)

    # Accept connection
    await connection_manager.connect(websocket, user_id, conversation_id)

    # Send welcome message
    welcome_message = {
        "type": MessageType.CONNECTION,
        "payload": {
            "status": "connected",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to MAGPIE WebSocket server"
        }
    }
    await connection_manager.send_personal_message(websocket, welcome_message)

    try:
        # Main message loop
        while True:
            # Receive message
            data = await websocket.receive_text()

            try:
                # Parse message
                message_data = json.loads(data)
                message_type = message_data.get("type")
                payload = message_data.get("payload", {})

                # Handle different message types
                if message_type == MessageType.MESSAGE:
                    await handle_chat_message(websocket, user_id, payload)
                elif message_type == MessageType.TYPING:
                    await handle_typing_indicator(websocket, user_id, payload)
                elif message_type == "join_conversation":
                    await handle_join_conversation(websocket, user_id, payload)
                elif message_type == "leave_conversation":
                    await handle_leave_conversation(websocket, user_id, payload)
                elif message_type == MessageType.FEEDBACK:
                    await handle_feedback(websocket, user_id, payload)
                else:
                    # Unknown message type
                    error_message = {
                        "type": MessageType.ERROR,
                        "payload": {
                            "error": {
                                "code": "unknown_message_type",
                                "message": f"Unknown message type: {message_type}"
                            }
                        }
                    }
                    await connection_manager.send_personal_message(websocket, error_message)

            except json.JSONDecodeError:
                # Invalid JSON
                error_message = {
                    "type": MessageType.ERROR,
                    "payload": {
                        "error": {
                            "code": "invalid_json",
                            "message": "Invalid JSON format"
                        }
                    }
                }
                await connection_manager.send_personal_message(websocket, error_message)

            except ValidationError as e:
                # Invalid message format
                error_message = {
                    "type": MessageType.ERROR,
                    "payload": {
                        "error": {
                            "code": "validation_error",
                            "message": str(e)
                        }
                    }
                }
                await connection_manager.send_personal_message(websocket, error_message)

            except Exception as e:
                # Other errors
                logger.error(f"Error handling WebSocket message: {str(e)}")
                error_message = {
                    "type": MessageType.ERROR,
                    "payload": {
                        "error": {
                            "code": "server_error",
                            "message": "Internal server error"
                        }
                    }
                }
                await connection_manager.send_personal_message(websocket, error_message)

    except WebSocketDisconnect:
        # Client disconnected
        connection_manager.disconnect(websocket)
        logger.info(f"WebSocket client disconnected: {user_id}")


async def handle_chat_message(websocket: WebSocket, user_id: str, payload: Dict[str, Any]):
    """
    Handle chat message.

    Args:
        websocket: WebSocket connection
        user_id: User ID
        payload: Message payload
    """
    # Extract data from payload
    message_text = payload.get("message")
    conversation_id = payload.get("conversation_id")
    force_agent_type = payload.get("force_agent_type")

    if not message_text:
        # Missing message text
        error_message = {
            "type": MessageType.ERROR,
            "payload": {
                "error": {
                    "code": "missing_message",
                    "message": "Message text is required"
                }
            }
        }
        await connection_manager.send_personal_message(websocket, error_message)
        return

    if not conversation_id:
        # Missing conversation ID
        error_message = {
            "type": MessageType.ERROR,
            "payload": {
                "error": {
                    "code": "missing_conversation_id",
                    "message": "Conversation ID is required"
                }
            }
        }
        await connection_manager.send_personal_message(websocket, error_message)
        return

    # Create user message
    user_message_id = f"msg-{uuid.uuid4()}"
    user_message = {
        "id": user_message_id,
        "content": message_text,
        "role": "user",
        "timestamp": datetime.now().isoformat()
    }

    # Broadcast user message to conversation
    user_message_event = {
        "type": MessageType.MESSAGE,
        "payload": {
            "message": user_message,
            "conversation_id": conversation_id
        }
    }
    await connection_manager.broadcast_to_conversation(conversation_id, user_message_event)

    # Send typing indicator
    typing_event = {
        "type": MessageType.TYPING,
        "payload": {
            "is_typing": True,
            "conversation_id": conversation_id,
            "agent_type": force_agent_type
        }
    }
    await connection_manager.broadcast_to_conversation(conversation_id, typing_event)

    # For now, use mock data service to generate a response
    # In a real implementation, this would call the appropriate agent service
    try:
        # Determine agent type based on message or forced type
        agent_type = force_agent_type or "documentation"  # Default to documentation

        # Get mock response
        mock_response = mock_data_service.get_mock_response(
            message_text,
            agent_type=agent_type,
            conversation_id=conversation_id
        )

        # Stop typing indicator
        typing_event["payload"]["is_typing"] = False
        await connection_manager.broadcast_to_conversation(conversation_id, typing_event)

        # Create assistant message
        assistant_message = {
            "id": f"msg-{uuid.uuid4()}",
            "content": mock_response.get("response", "I'm not sure how to respond to that."),
            "role": "assistant",
            "timestamp": datetime.now().isoformat(),
            "agent_type": mock_response.get("agentType", agent_type),
            "confidence": mock_response.get("confidence", 0.8)
        }

        # Broadcast assistant message to conversation
        assistant_message_event = {
            "type": MessageType.MESSAGE,
            "payload": {
                "message": assistant_message,
                "conversation_id": conversation_id
            }
        }
        await connection_manager.broadcast_to_conversation(conversation_id, assistant_message_event)

    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")

        # Stop typing indicator
        typing_event["payload"]["is_typing"] = False
        await connection_manager.broadcast_to_conversation(conversation_id, typing_event)

        # Send error message
        error_message = {
            "type": MessageType.ERROR,
            "payload": {
                "error": {
                    "code": "response_generation_error",
                    "message": "Error generating response"
                },
                "conversation_id": conversation_id
            }
        }
        await connection_manager.broadcast_to_conversation(conversation_id, error_message)


async def handle_typing_indicator(websocket: WebSocket, user_id: str, payload: Dict[str, Any]):
    """
    Handle typing indicator.

    Args:
        websocket: WebSocket connection
        user_id: User ID
        payload: Message payload
    """
    # Extract data from payload
    is_typing = payload.get("is_typing", False)
    conversation_id = payload.get("conversation_id")

    if not conversation_id:
        # Missing conversation ID
        error_message = {
            "type": MessageType.ERROR,
            "payload": {
                "error": {
                    "code": "missing_conversation_id",
                    "message": "Conversation ID is required"
                }
            }
        }
        await connection_manager.send_personal_message(websocket, error_message)
        return

    # Broadcast typing indicator to conversation
    typing_event = {
        "type": MessageType.TYPING,
        "payload": {
            "is_typing": is_typing,
            "conversation_id": conversation_id,
            "user_id": user_id
        }
    }
    await connection_manager.broadcast_to_conversation(conversation_id, typing_event, exclude_user=user_id)


async def handle_join_conversation(websocket: WebSocket, user_id: str, payload: Dict[str, Any]):
    """
    Handle join conversation.

    Args:
        websocket: WebSocket connection
        user_id: User ID
        payload: Message payload
    """
    # Extract data from payload
    conversation_id = payload.get("conversation_id")

    if not conversation_id:
        # Missing conversation ID
        error_message = {
            "type": MessageType.ERROR,
            "payload": {
                "error": {
                    "code": "missing_conversation_id",
                    "message": "Conversation ID is required"
                }
            }
        }
        await connection_manager.send_personal_message(websocket, error_message)
        return

    # Join conversation
    await connection_manager.join_conversation(websocket, conversation_id)


async def handle_leave_conversation(websocket: WebSocket, user_id: str, payload: Dict[str, Any]):
    """
    Handle leave conversation.

    Args:
        websocket: WebSocket connection
        user_id: User ID
        payload: Message payload
    """
    # Leave conversation
    await connection_manager.leave_conversation(websocket)


async def handle_feedback(websocket: WebSocket, user_id: str, payload: Dict[str, Any]):
    """
    Handle feedback.

    Args:
        websocket: WebSocket connection
        user_id: User ID
        payload: Message payload
    """
    # Extract data from payload
    message_id = payload.get("message_id")
    feedback = payload.get("feedback")
    comments = payload.get("comments")

    if not message_id or not feedback:
        # Missing required fields
        error_message = {
            "type": MessageType.ERROR,
            "payload": {
                "error": {
                    "code": "missing_feedback_fields",
                    "message": "Message ID and feedback are required"
                }
            }
        }
        await connection_manager.send_personal_message(websocket, error_message)
        return

    # In a real implementation, this would store the feedback in the database
    # For now, just acknowledge receipt
    feedback_received = {
        "type": "feedback_received",
        "payload": {
            "message_id": message_id,
            "status": "success"
        }
    }
    await connection_manager.send_personal_message(websocket, feedback_received)
