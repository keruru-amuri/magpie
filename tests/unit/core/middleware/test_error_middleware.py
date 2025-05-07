"""
Unit tests for error middleware.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request, Response
from starlette.datastructures import Address
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from app.core.middleware import ErrorHandlingMiddleware


@pytest.fixture
def mock_app():
    """Create a mock FastAPI application."""
    return MagicMock(spec=FastAPI)


@pytest.fixture
def mock_request():
    """Create a mock request object."""
    request = MagicMock(spec=Request)
    request.method = "GET"
    request.url.path = "/test"
    request.client = Address("127.0.0.1", 8000)
    request.state = MagicMock()
    request.state.request_id = str(uuid.uuid4())
    request.headers = {"user-agent": "test-agent"}
    return request


@pytest.mark.asyncio
async def test_error_middleware_success(mock_app, mock_request):
    """Test that ErrorHandlingMiddleware passes through successful requests."""
    # Create a mock response
    mock_response = MagicMock(spec=Response)

    # Create a mock call_next function that returns the mock response
    call_next = AsyncMock(return_value=mock_response)

    # Create middleware
    middleware = ErrorHandlingMiddleware(mock_app)

    # Call middleware
    response = await middleware.dispatch(mock_request, call_next)

    # Check that call_next was called with the request
    call_next.assert_called_once_with(mock_request)

    # Check that the response was returned
    assert response == mock_response


@pytest.mark.asyncio
async def test_error_middleware_exception(mock_app, mock_request):
    """Test that ErrorHandlingMiddleware handles exceptions."""
    # Create a mock call_next function that raises an exception
    exception = ValueError("Test exception")
    call_next = AsyncMock(side_effect=exception)

    # Create middleware
    middleware = ErrorHandlingMiddleware(mock_app)

    # Mock track_error
    with patch("app.core.middleware.error_middleware.track_error") as mock_track_error:
        # Create a mock error event
        mock_error_event = MagicMock()
        mock_error_event.id = "test_error_id"
        mock_track_error.return_value = mock_error_event

        # Call middleware
        response = await middleware.dispatch(mock_request, call_next)

        # Check that call_next was called with the request
        call_next.assert_called_once_with(mock_request)

        # Check that track_error was called
        mock_track_error.assert_called_once()

        # Check kwargs instead of args since the implementation might use kwargs
        _, kwargs = mock_track_error.call_args
        assert kwargs.get("message") == "Test exception"
        assert kwargs.get("exception") == exception
        assert kwargs.get("component") == "api"
        assert kwargs.get("request_id") == mock_request.state.request_id

        # Check that a JSON response was returned
        assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        # JSONResponse stores content in the body attribute
        assert b'"detail"' in response.body
        assert b'"error_id"' in response.body
        assert b'"request_id"' in response.body
