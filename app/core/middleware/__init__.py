"""
Middleware package for the MAGPIE platform.

This package contains middleware components for the MAGPIE platform.
"""

from app.core.middleware.logging_middleware import LoggingMiddleware, RequestIdMiddleware
from app.core.middleware.error_middleware import ErrorHandlingMiddleware
from app.core.middleware.profiling_middleware import ProfilingMiddleware

__all__ = [
    "LoggingMiddleware",
    "RequestIdMiddleware",
    "ErrorHandlingMiddleware",
    "ProfilingMiddleware",
]
