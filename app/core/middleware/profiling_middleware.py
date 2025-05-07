"""
Profiling middleware for the MAGPIE platform.

This middleware profiles API requests and records performance metrics.
"""

import time
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.monitoring.profiling import record_api_request

# Configure logging
logger = logging.getLogger(__name__)


class ProfilingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for profiling API requests.

    This middleware records performance metrics for API requests.
    """

    def __init__(
        self,
        app: ASGIApp,
        enabled: bool = True,
    ):
        """
        Initialize profiling middleware.

        Args:
            app: ASGI application
            enabled: Whether profiling is enabled
        """
        super().__init__(app)
        self.enabled = enabled
        self.logger = logger

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Process a request and record performance metrics.

        Args:
            request: FastAPI request
            call_next: Next middleware in the chain

        Returns:
            Response: FastAPI response
        """
        # Skip profiling if disabled
        if not self.enabled:
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Record error
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"Error processing request: {str(e)}",
                request_path=request.url.path,
                request_method=request.method,
                duration_ms=duration_ms,
                error=str(e),
            )
            raise

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Record API request
        try:
            record_api_request(
                request=request,
                response=response,
                duration_ms=duration_ms,
                endpoint=request.url.path,
            )
        except Exception as e:
            self.logger.error(f"Error recording API request: {str(e)}")

        # Return response
        return response
