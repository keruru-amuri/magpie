"""
Error handling middleware for the MAGPIE platform.

This module provides middleware for capturing and tracking exceptions.
"""

import traceback
from typing import Callable, Dict, Any, Optional

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from app.core.monitoring import (
    ErrorSeverity,
    ErrorCategory,
    track_error,
)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for capturing and tracking exceptions.
    
    This middleware captures unhandled exceptions, logs them,
    and tracks them in the error tracking system.
    """
    
    def __init__(self, app):
        """
        Initialize the middleware.
        
        Args:
            app: ASGI application
        """
        super().__init__(app)
        self.logger = logger.bind(name=__name__)
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process the request and handle exceptions.
        
        Args:
            request: FastAPI request
            call_next: Next middleware or route handler
            
        Returns:
            Response: FastAPI response
        """
        try:
            # Process the request
            return await call_next(request)
        except Exception as e:
            # Get request ID from state if available
            request_id = getattr(request.state, "request_id", None)
            
            # Get user ID from state if available
            user_id = None
            if hasattr(request.state, "user"):
                user_id = getattr(request.state.user, "id", None)
            
            # Create context for error tracking
            context = {
                "path": request.url.path,
                "method": request.method,
                "client": request.client.host if request.client else "unknown",
                "headers": dict(request.headers),
            }
            
            # Track the error
            error_event = track_error(
                message=str(e),
                exception=e,
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.API,
                component="api",
                user_id=user_id,
                request_id=request_id,
                context=context,
                alert=True,
            )
            
            # Log the error
            self.logger.bind(
                error_id=error_event.id if error_event else None,
                request_id=request_id,
                user_id=user_id,
                path=request.url.path,
                method=request.method,
            ).exception(f"Unhandled exception: {e}")
            
            # Create error response
            error_detail = {
                "detail": "Internal server error",
            }
            
            # Add error ID if available
            if error_event:
                error_detail["error_id"] = error_event.id
            
            # Add request ID if available
            if request_id:
                error_detail["request_id"] = request_id
            
            # Create JSON response
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_detail,
            )
