"""
Logging middleware for the MAGPIE platform.

This module provides middleware for logging HTTP requests and responses
and collecting performance metrics.
"""

import json
import time
import uuid
from typing import Callable, Dict, Any, Optional, List, Set

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.monitoring.metrics import record_timing, record_count


class RequestIdMiddleware:
    """
    Middleware that adds a unique request ID to each request.

    This middleware generates a unique ID for each request and makes it
    available in the request state for logging and tracing purposes.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Generate a unique request ID
        request_id = str(uuid.uuid4())

        # Add request ID to scope state
        scope["state"] = scope.get("state", {})
        scope["state"]["request_id"] = request_id

        # Continue processing the request
        await self.app(scope, receive, send)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.

    This middleware logs information about incoming requests and outgoing
    responses, including timing information, status codes, and other metadata.
    It also collects performance metrics for analysis.
    """

    # Fields that may contain sensitive information and should be masked in logs
    SENSITIVE_FIELDS: Set[str] = {
        "password", "token", "secret", "key", "auth", "credential", "jwt",
        "api_key", "apikey", "access_token", "refresh_token", "private_key",
    }

    # Maximum content length to log (to avoid huge logs)
    MAX_CONTENT_LENGTH: int = 10000

    def __init__(self, app: ASGIApp):
        """
        Initialize the middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)
        self.logger = logger.bind(name=__name__)

    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mask sensitive data in request/response bodies.

        Args:
            data: Data to mask

        Returns:
            Dict[str, Any]: Masked data
        """
        if not isinstance(data, dict):
            return data

        masked_data = {}
        for key, value in data.items():
            # Check if the key contains sensitive information
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                masked_data[key] = "***MASKED***"
            elif isinstance(value, dict):
                # Recursively mask nested dictionaries
                masked_data[key] = self._mask_sensitive_data(value)
            elif isinstance(value, list):
                # Recursively mask items in lists
                masked_data[key] = [
                    self._mask_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked_data[key] = value

        return masked_data

    async def _get_request_body(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Get the request body safely.

        Args:
            request: FastAPI request

        Returns:
            Optional[Dict[str, Any]]: Request body as a dictionary, or None if not available
        """
        try:
            # Check content type
            content_type = request.headers.get("content-type", "").lower()

            # Only process JSON content
            if "application/json" in content_type:
                # Get request body
                body = await request.body()

                # Skip if body is too large
                if len(body) > self.MAX_CONTENT_LENGTH:
                    return {"message": f"Body too large ({len(body)} bytes)"}

                # Parse JSON body
                if body:
                    try:
                        body_dict = json.loads(body)
                        # Mask sensitive data
                        return self._mask_sensitive_data(body_dict)
                    except json.JSONDecodeError:
                        return {"message": "Invalid JSON body"}

            return None
        except Exception as e:
            self.logger.warning(f"Failed to get request body: {e}")
            return None

    async def _get_response_body(self, response: Response) -> Optional[Dict[str, Any]]:
        """
        Get the response body safely.

        Args:
            response: FastAPI response

        Returns:
            Optional[Dict[str, Any]]: Response body as a dictionary, or None if not available
        """
        try:
            # Check content type
            content_type = response.headers.get("content-type", "").lower()

            # Only process JSON content
            if "application/json" in content_type:
                # Get response body
                body = response.body

                # Skip if body is too large
                if len(body) > self.MAX_CONTENT_LENGTH:
                    return {"message": f"Body too large ({len(body)} bytes)"}

                # Parse JSON body
                if body:
                    try:
                        body_dict = json.loads(body)
                        # Mask sensitive data
                        return self._mask_sensitive_data(body_dict)
                    except json.JSONDecodeError:
                        return {"message": "Invalid JSON body"}

            return None
        except Exception as e:
            self.logger.warning(f"Failed to get response body: {e}")
            return None

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Get request ID from state or generate a new one
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

        # Create a logger with request context
        request_logger = logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown",
        )

        # Log request
        request_logger.info(f"Request started: {request.method} {request.url.path}")

        # Process request and measure timing
        start_time = time.time()

        # Record request count metric
        record_count(
            name="http_requests_total",
            tags={
                "method": request.method,
                "path": request.url.path,
            }
        )

        try:
            # Get request body for logging if needed
            request_body = await self._get_request_body(request)

            # Process the request
            response = await call_next(request)

            # Calculate request processing time
            process_time = time.time() - start_time
            process_time_ms = process_time * 1000  # Convert to milliseconds

            # Get response body for logging if needed
            response_body = await self._get_response_body(response)

            # Record timing metric
            record_timing(
                name="http_request_duration_milliseconds",
                start_time=start_time,
                tags={
                    "method": request.method,
                    "path": request.url.path,
                    "status": str(response.status_code),
                }
            )

            # Record status code metric
            record_count(
                name="http_responses_total",
                tags={
                    "method": request.method,
                    "path": request.url.path,
                    "status": str(response.status_code),
                }
            )

            # Log response with additional context
            log_context = {
                "status_code": response.status_code,
                "processing_time_ms": process_time_ms,
                "content_length": len(response.body) if hasattr(response, "body") else 0,
            }

            # Add request/response bodies if available
            if request_body:
                log_context["request_body"] = request_body
            if response_body:
                log_context["response_body"] = response_body

            # Log response
            request_logger.bind(**log_context).info(
                f"Request completed: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Time: {process_time:.4f}s"
            )

            # Add custom headers
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate request processing time
            process_time = time.time() - start_time
            process_time_ms = process_time * 1000  # Convert to milliseconds

            # Record error metric
            record_count(
                name="http_errors_total",
                tags={
                    "method": request.method,
                    "path": request.url.path,
                    "error": type(e).__name__,
                }
            )

            # Log exception with additional context
            request_logger.bind(
                processing_time_ms=process_time_ms,
                exception_type=type(e).__name__,
                exception_message=str(e),
            ).exception(f"Request failed: {request.method} {request.url.path}")

            # Re-raise the exception
            raise
