"""WebSocket package for MAGPIE platform."""

from app.core.websocket.connection import connection_manager, ConnectionManager

__all__ = ["connection_manager", "ConnectionManager"]
