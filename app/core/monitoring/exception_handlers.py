"""
Exception handlers for the MAGPIE platform.

This module provides utility functions for handling exceptions in routes.
"""

import asyncio
import functools
from typing import Callable, Dict, Any, Optional, TypeVar, Awaitable, Union, Type

from fastapi import Request, Response, HTTPException
from loguru import logger
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from app.core.monitoring.error_tracking import (
    ErrorSeverity,
    ErrorCategory,
    track_error,
)


# Type variables for function signatures
T = TypeVar("T")
AsyncFunc = Callable[..., Awaitable[T]]
SyncFunc = Callable[..., T]
AnyFunc = Union[AsyncFunc[T], SyncFunc[T]]


def handle_exceptions(
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    category: ErrorCategory = ErrorCategory.API,
    component: str = "api",
    alert: bool = True,
    reraise: bool = True,
    exclude_exceptions: Optional[list[Type[Exception]]] = None,
) -> Callable[[AnyFunc[T]], AnyFunc[T]]:
    """
    Decorator for handling exceptions in route handlers.

    This decorator catches exceptions, logs them, and tracks them in the error tracking system.
    It can be used with both synchronous and asynchronous functions.

    Args:
        severity: Severity level of the error
        category: Category of the error
        component: Component where the error occurred
        alert: Whether to trigger alerts for this error
        reraise: Whether to re-raise the exception after tracking
        exclude_exceptions: List of exception types to exclude from tracking

    Returns:
        Callable: Decorated function
    """
    exclude_exceptions = exclude_exceptions or [HTTPException]

    def decorator(func: AnyFunc[T]) -> AnyFunc[T]:
        """
        Decorator function.

        Args:
            func: Function to decorate

        Returns:
            Callable: Decorated function
        """
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                """
                Asynchronous wrapper function.

                Args:
                    *args: Positional arguments
                    **kwargs: Keyword arguments

                Returns:
                    T: Function result

                Raises:
                    Exception: Re-raised exception if reraise is True
                """
                try:
                    return await func(*args, **kwargs)
                except tuple(exclude_exceptions) as e:
                    # Re-raise excluded exceptions without tracking
                    raise
                except Exception as e:
                    # Extract request and user information if available
                    request = None
                    user_id = None
                    request_id = None

                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            request_id = getattr(request.state, "request_id", None)
                            if hasattr(request.state, "user"):
                                user_id = getattr(request.state.user, "id", None)
                            break

                    # Create context for error tracking
                    context = {
                        "function": func.__name__,
                        "module": func.__module__,
                    }

                    # Extract request information if available
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            context.update({
                                "path": request.url.path,
                                "method": request.method,
                                "client": request.client.host if request.client else "unknown",
                            })
                            break

                    # Track the error
                    error_event = track_error(
                        message=str(e),
                        exception=e,
                        severity=severity,
                        category=category,
                        component=component,
                        user_id=user_id,
                        request_id=request_id,
                        context=context,
                        alert=alert,
                    )

                    # Log the error
                    logger.bind(
                        error_id=error_event.id if error_event else None,
                        request_id=request_id,
                        user_id=user_id,
                        function=func.__name__,
                        module=func.__module__,
                    ).exception(f"Exception in {func.__name__}: {e}")

                    # Re-raise the exception if requested
                    if reraise:
                        raise

                    # Return a default response if not re-raising
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                        content={"detail": "Internal server error"},
                    )

            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> T:
                """
                Synchronous wrapper function.

                Args:
                    *args: Positional arguments
                    **kwargs: Keyword arguments

                Returns:
                    T: Function result

                Raises:
                    Exception: Re-raised exception if reraise is True
                """
                try:
                    return func(*args, **kwargs)
                except tuple(exclude_exceptions) as e:
                    # Re-raise excluded exceptions without tracking
                    raise
                except Exception as e:
                    # Extract request and user information if available
                    request = None
                    user_id = None
                    request_id = None

                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            request_id = getattr(request.state, "request_id", None)
                            if hasattr(request.state, "user"):
                                user_id = getattr(request.state.user, "id", None)
                            break

                    # Create context for error tracking
                    context = {
                        "function": func.__name__,
                        "module": func.__module__,
                    }

                    # Extract request information if available
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            context.update({
                                "path": request.url.path,
                                "method": request.method,
                                "client": request.client.host if request.client else "unknown",
                            })
                            break

                    # Track the error
                    error_event = track_error(
                        message=str(e),
                        exception=e,
                        severity=severity,
                        category=category,
                        component=component,
                        user_id=user_id,
                        request_id=request_id,
                        context=context,
                        alert=alert,
                    )

                    # Log the error
                    logger.bind(
                        error_id=error_event.id if error_event else None,
                        request_id=request_id,
                        user_id=user_id,
                        function=func.__name__,
                        module=func.__module__,
                    ).exception(f"Exception in {func.__name__}: {e}")

                    # Re-raise the exception if requested
                    if reraise:
                        raise

                    # Return a default response if not re-raising
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                        content={"detail": "Internal server error"},
                    )

            return sync_wrapper

    return decorator
