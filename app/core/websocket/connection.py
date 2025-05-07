"""
WebSocket connection manager for MAGPIE platform.

This module provides a connection manager for WebSocket connections.
"""

import json
import logging
from typing import Dict, List, Optional, Set, Any, Union

from fastapi import WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel

from app.core.logging import get_logger

# Configure logger
logger = get_logger(__name__)


class ConnectionManager:
    """
    WebSocket connection manager.

    This class manages WebSocket connections, including:
    - Accepting connections
    - Disconnecting clients
    - Broadcasting messages to all clients
    - Sending messages to specific clients
    - Managing conversation groups
    """

    def __init__(self):
        """Initialize the connection manager."""
        # All active connections
        self.active_connections: List[WebSocket] = []

        # Map of user_id to connections
        self.user_connections: Dict[str, List[WebSocket]] = {}

        # Map of conversation_id to set of user_ids
        self.conversation_users: Dict[str, Set[str]] = {}

        # Map of websocket to user_id
        self.connection_user_map: Dict[WebSocket, str] = {}

        # Map of websocket to conversation_id
        self.connection_conversation_map: Dict[WebSocket, str] = {}

        logger.info("WebSocket connection manager initialized")

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> None:
        """
        Accept a WebSocket connection and register it.

        Args:
            websocket: WebSocket connection
            user_id: User ID
            conversation_id: Optional conversation ID
        """
        # Accept the connection
        await websocket.accept()

        # Add to active connections
        self.active_connections.append(websocket)

        # Map connection to user
        self.connection_user_map[websocket] = user_id

        # Add to user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)

        # Add to conversation if provided
        if conversation_id:
            await self.join_conversation(websocket, conversation_id)

        logger.info(f"WebSocket connection accepted for user {user_id}")

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Disconnect a WebSocket connection and remove it from all registries.

        Args:
            websocket: WebSocket connection to disconnect
        """
        # Remove from active connections
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # Get user_id and conversation_id
        user_id = self.connection_user_map.get(websocket)
        conversation_id = self.connection_conversation_map.get(websocket)

        # Remove from user connections
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        # Remove from conversation
        if conversation_id and user_id:
            if conversation_id in self.conversation_users and user_id in self.conversation_users[conversation_id]:
                # Check if this was the last connection for this user in this conversation
                user_has_other_connections_in_conversation = False
                if user_id in self.user_connections:
                    for conn in self.user_connections[user_id]:
                        if conn != websocket and self.connection_conversation_map.get(conn) == conversation_id:
                            user_has_other_connections_in_conversation = True
                            break

                if not user_has_other_connections_in_conversation:
                    self.conversation_users[conversation_id].remove(user_id)
                    if not self.conversation_users[conversation_id]:
                        del self.conversation_users[conversation_id]

        # Remove from maps
        if websocket in self.connection_user_map:
            del self.connection_user_map[websocket]

        if websocket in self.connection_conversation_map:
            del self.connection_conversation_map[websocket]

        logger.info(f"WebSocket connection disconnected for user {user_id}")

    async def join_conversation(self, websocket: WebSocket, conversation_id: str) -> None:
        """
        Add a connection to a conversation group.

        Args:
            websocket: WebSocket connection
            conversation_id: Conversation ID
        """
        # Get user_id
        user_id = self.connection_user_map.get(websocket)
        if not user_id:
            logger.warning("Cannot join conversation: WebSocket not registered with a user_id")
            return

        # Add to conversation users
        if conversation_id not in self.conversation_users:
            self.conversation_users[conversation_id] = set()
        self.conversation_users[conversation_id].add(user_id)

        # Map connection to conversation
        self.connection_conversation_map[websocket] = conversation_id

        logger.info(f"User {user_id} joined conversation {conversation_id}")

        # Notify other users in the conversation
        await self.broadcast_to_conversation(
            conversation_id,
            {
                "type": "user_joined",
                "payload": {
                    "user_id": user_id,
                    "conversation_id": conversation_id
                }
            },
            exclude_user=user_id
        )

    async def leave_conversation(self, websocket: WebSocket) -> None:
        """
        Remove a connection from its conversation group.

        Args:
            websocket: WebSocket connection
        """
        # Get user_id and conversation_id
        user_id = self.connection_user_map.get(websocket)
        conversation_id = self.connection_conversation_map.get(websocket)

        if not user_id or not conversation_id:
            logger.warning("Cannot leave conversation: WebSocket not registered with a user_id or conversation_id")
            return

        # Check if this was the last connection for this user in this conversation
        user_has_other_connections_in_conversation = False
        if user_id in self.user_connections:
            for conn in self.user_connections[user_id]:
                if conn != websocket and self.connection_conversation_map.get(conn) == conversation_id:
                    user_has_other_connections_in_conversation = True
                    break

        # Remove from conversation users if this was the last connection
        if not user_has_other_connections_in_conversation:
            if conversation_id in self.conversation_users and user_id in self.conversation_users[conversation_id]:
                self.conversation_users[conversation_id].remove(user_id)
                if not self.conversation_users[conversation_id]:
                    del self.conversation_users[conversation_id]

                # Notify other users in the conversation
                await self.broadcast_to_conversation(
                    conversation_id,
                    {
                        "type": "user_left",
                        "payload": {
                            "user_id": user_id,
                            "conversation_id": conversation_id
                        }
                    }
                )

        # Remove from connection map
        if websocket in self.connection_conversation_map:
            del self.connection_conversation_map[websocket]

        logger.info(f"User {user_id} left conversation {conversation_id}")

    async def send_personal_message(self, websocket: WebSocket, message: Union[str, dict]) -> None:
        """
        Send a message to a specific WebSocket connection.

        Args:
            websocket: WebSocket connection
            message: Message to send (string or dict)
        """
        if isinstance(message, dict):
            await websocket.send_json(message)
        else:
            await websocket.send_text(message)

    async def broadcast(self, message: Union[str, dict], exclude: Optional[WebSocket] = None) -> None:
        """
        Broadcast a message to all active connections.

        Args:
            message: Message to broadcast (string or dict)
            exclude: Optional WebSocket connection to exclude
        """
        for connection in self.active_connections:
            if connection != exclude:
                try:
                    await self.send_personal_message(connection, message)
                except Exception as e:
                    logger.error(f"Error broadcasting message: {str(e)}")
                    # Connection might be closed, remove it
                    self.disconnect(connection)

    async def broadcast_to_user(self, user_id: str, message: Union[str, dict]) -> None:
        """
        Broadcast a message to all connections for a specific user.

        Args:
            user_id: User ID
            message: Message to broadcast (string or dict)
        """
        if user_id not in self.user_connections:
            logger.warning(f"Cannot broadcast to user {user_id}: No active connections")
            return

        for connection in self.user_connections[user_id]:
            try:
                await self.send_personal_message(connection, message)
            except Exception as e:
                logger.error(f"Error broadcasting message to user {user_id}: {str(e)}")
                # Connection might be closed, remove it
                self.disconnect(connection)

    async def broadcast_to_conversation(
        self,
        conversation_id: str,
        message: Union[str, dict],
        exclude_user: Optional[str] = None
    ) -> None:
        """
        Broadcast a message to all users in a conversation.

        Args:
            conversation_id: Conversation ID
            message: Message to broadcast (string or dict)
            exclude_user: Optional user ID to exclude
        """
        if conversation_id not in self.conversation_users:
            logger.warning(f"Cannot broadcast to conversation {conversation_id}: No active users")
            return

        for user_id in self.conversation_users[conversation_id]:
            if user_id != exclude_user and user_id in self.user_connections:
                for connection in self.user_connections[user_id]:
                    if self.connection_conversation_map.get(connection) == conversation_id:
                        try:
                            await self.send_personal_message(connection, message)
                        except Exception as e:
                            logger.error(f"Error broadcasting message to conversation {conversation_id}: {str(e)}")
                            # Connection might be closed, remove it
                            self.disconnect(connection)

    def get_active_users_in_conversation(self, conversation_id: str) -> List[str]:
        """
        Get a list of active user IDs in a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            List[str]: List of user IDs
        """
        if conversation_id not in self.conversation_users:
            return []

        return list(self.conversation_users[conversation_id])

    def get_active_conversations_for_user(self, user_id: str) -> List[str]:
        """
        Get a list of active conversation IDs for a user.

        Args:
            user_id: User ID

        Returns:
            List[str]: List of conversation IDs
        """
        conversations = []

        for conversation_id, users in self.conversation_users.items():
            if user_id in users:
                conversations.append(conversation_id)

        return conversations


# Create a singleton instance
connection_manager = ConnectionManager()
