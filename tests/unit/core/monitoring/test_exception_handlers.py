"""
Unit tests for exception handlers.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from app.core.monitoring import (
    ErrorSeverity,
    ErrorCategory,
    handle_exceptions,
)


def test_handle_exceptions_sync():
    """Test that handle_exceptions works correctly with synchronous functions."""
    # Create a test function
    @handle_exceptions(
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
        alert=True,
        reraise=True,
    )
    def test_function(arg1, arg2=None):
        if arg2 is None:
            raise ValueError("Test exception")
        return arg1 + arg2

    # Test successful execution
    result = test_function(1, 2)
    assert result == 3

    # Test exception handling
    with patch("app.core.monitoring.exception_handlers.track_error") as mock_track_error:
        # Create a mock error event
        mock_error_event = MagicMock()
        mock_error_event.id = "test_error_id"
        mock_track_error.return_value = mock_error_event

        # Call function and expect exception
        with pytest.raises(ValueError):
            test_function(1)

        # Check that track_error was called
        mock_track_error.assert_called_once()

        # Check kwargs instead of args since the implementation might use kwargs
        _, kwargs = mock_track_error.call_args
        assert kwargs.get("message") == "Test exception"
        assert isinstance(kwargs.get("exception"), ValueError)
        assert kwargs.get("severity") == ErrorSeverity.ERROR
        assert kwargs.get("category") == ErrorCategory.API
        assert kwargs.get("component") == "test_component"
        assert kwargs.get("alert") is True


@pytest.mark.asyncio
async def test_handle_exceptions_async():
    """Test that handle_exceptions works correctly with asynchronous functions."""
    # Create a test function
    @handle_exceptions(
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
        alert=True,
        reraise=True,
    )
    async def test_function(arg1, arg2=None):
        await asyncio.sleep(0.01)
        if arg2 is None:
            raise ValueError("Test exception")
        return arg1 + arg2

    # Test successful execution
    result = await test_function(1, 2)
    assert result == 3

    # Test exception handling
    with patch("app.core.monitoring.exception_handlers.track_error") as mock_track_error:
        # Create a mock error event
        mock_error_event = MagicMock()
        mock_error_event.id = "test_error_id"
        mock_track_error.return_value = mock_error_event

        # Call function and expect exception
        with pytest.raises(ValueError):
            await test_function(1)

        # Check that track_error was called
        mock_track_error.assert_called_once()

        # Check kwargs instead of args since the implementation might use kwargs
        _, kwargs = mock_track_error.call_args
        assert kwargs.get("message") == "Test exception"
        assert isinstance(kwargs.get("exception"), ValueError)
        assert kwargs.get("severity") == ErrorSeverity.ERROR
        assert kwargs.get("category") == ErrorCategory.API
        assert kwargs.get("component") == "test_component"
        assert kwargs.get("alert") is True


def test_handle_exceptions_with_request():
    """Test that handle_exceptions works correctly with request objects."""
    # Create a mock request
    mock_request = MagicMock(spec=Request)
    mock_request.method = "GET"
    mock_request.url.path = "/test"
    mock_request.client.host = "127.0.0.1"
    mock_request.state.request_id = "test_request_id"
    mock_request.state.user = MagicMock()
    mock_request.state.user.id = "test_user_id"

    # Create a test function
    @handle_exceptions(
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
        alert=True,
        reraise=True,
    )
    def test_function(request, arg1, arg2=None):
        if arg2 is None:
            raise ValueError("Test exception")
        return arg1 + arg2

    # Test exception handling
    with patch("app.core.monitoring.exception_handlers.track_error") as mock_track_error:
        # Create a mock error event
        mock_error_event = MagicMock()
        mock_error_event.id = "test_error_id"
        mock_track_error.return_value = mock_error_event

        # Call function and expect exception
        with pytest.raises(ValueError):
            test_function(mock_request, 1)

        # Check that track_error was called with request information
        mock_track_error.assert_called_once()

        # Check kwargs instead of args since the implementation might use kwargs
        _, kwargs = mock_track_error.call_args
        assert kwargs.get("message") == "Test exception"
        assert isinstance(kwargs.get("exception"), ValueError)
        assert kwargs.get("user_id") == "test_user_id"
        assert kwargs.get("request_id") == "test_request_id"
        assert "path" in kwargs.get("context", {})
        assert "method" in kwargs.get("context", {})
        assert "client" in kwargs.get("context", {})


def test_handle_exceptions_exclude():
    """Test that handle_exceptions correctly excludes specified exceptions."""
    # Create a test function
    @handle_exceptions(
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
        alert=True,
        reraise=True,
        exclude_exceptions=[ValueError],
    )
    def test_function(arg1, arg2=None):
        if arg2 is None:
            raise ValueError("Test exception")
        return arg1 + arg2

    # Test exception handling
    with patch("app.core.monitoring.exception_handlers.track_error") as mock_track_error:
        # Call function and expect exception
        with pytest.raises(ValueError):
            test_function(1)

        # Check that track_error was not called
        mock_track_error.assert_not_called()


def test_handle_exceptions_http_exception():
    """Test that handle_exceptions correctly excludes HTTPException by default."""
    # Create a test function
    @handle_exceptions(
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
        alert=True,
        reraise=True,
    )
    def test_function(arg1, arg2=None):
        if arg2 is None:
            raise HTTPException(status_code=404, detail="Not found")
        return arg1 + arg2

    # Test exception handling
    with patch("app.core.monitoring.exception_handlers.track_error") as mock_track_error:
        # Call function and expect exception
        with pytest.raises(HTTPException):
            test_function(1)

        # Check that track_error was not called
        mock_track_error.assert_not_called()


def test_handle_exceptions_no_reraise():
    """Test that handle_exceptions works correctly when reraise is False."""
    # Create a test function
    @handle_exceptions(
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
        alert=True,
        reraise=False,
    )
    def test_function(arg1, arg2=None):
        if arg2 is None:
            raise ValueError("Test exception")
        return arg1 + arg2

    # Test exception handling
    with patch("app.core.monitoring.exception_handlers.track_error") as mock_track_error:
        # Create a mock error event
        mock_error_event = MagicMock()
        mock_error_event.id = "test_error_id"
        mock_track_error.return_value = mock_error_event

        # Call function and expect a response instead of an exception
        response = test_function(1)

        # Check that track_error was called
        mock_track_error.assert_called_once()

        # Check that a response was returned
        assert response.status_code == 500
        assert response.body == b'{"detail":"Internal server error"}'
