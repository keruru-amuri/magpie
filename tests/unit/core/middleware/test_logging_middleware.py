"""
Unit tests for logging middleware.
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request, Response
from starlette.datastructures import Address

from app.core.middleware import LoggingMiddleware, RequestIdMiddleware


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
    return request


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = MagicMock(spec=Response)
    response.status_code = 200
    response.headers = {}
    return response


@pytest.mark.asyncio
async def test_request_id_middleware():
    """Test that RequestIdMiddleware adds a request ID to the scope state."""
    # Create a mock app and scope
    app = AsyncMock()
    scope = {"type": "http", "state": {}}
    receive = AsyncMock()
    send = AsyncMock()

    # Create middleware
    middleware = RequestIdMiddleware(app)

    # Call middleware
    await middleware(scope, receive, send)

    # Check that app was called with the scope
    app.assert_called_once_with(scope, receive, send)

    # Check that request_id was added to scope state
    assert "request_id" in scope["state"]
    assert isinstance(scope["state"]["request_id"], str)
    assert len(scope["state"]["request_id"]) > 0


@pytest.mark.asyncio
async def test_request_id_middleware_non_http():
    """Test that RequestIdMiddleware ignores non-HTTP requests."""
    # Create a mock app and scope
    app = AsyncMock()
    scope = {"type": "websocket", "state": {}}
    receive = AsyncMock()
    send = AsyncMock()

    # Create middleware
    middleware = RequestIdMiddleware(app)

    # Call middleware
    await middleware(scope, receive, send)

    # Check that app was called with the scope
    app.assert_called_once_with(scope, receive, send)

    # Check that request_id was not added to scope state
    assert "request_id" not in scope.get("state", {})


@pytest.mark.asyncio
async def test_logging_middleware_success(mock_request, mock_response):
    """Test that LoggingMiddleware logs successful requests."""
    # Create a mock call_next function
    call_next = AsyncMock(return_value=mock_response)

    # Set up mock request and response
    mock_request.headers = {"content-type": "application/json"}
    mock_request.body = AsyncMock(return_value=b'{"test": "data"}')
    mock_response.headers = {"content-type": "application/json"}
    mock_response.body = b'{"result": "success"}'

    # Create middleware
    middleware = LoggingMiddleware(None)

    # Mock logger and metrics
    with patch("app.core.middleware.logging_middleware.logger") as mock_logger, \
         patch("app.core.middleware.logging_middleware.record_timing") as mock_record_timing, \
         patch("app.core.middleware.logging_middleware.record_count") as mock_record_count:

        # Create mock bound logger
        mock_bound_logger = MagicMock()
        mock_logger.bind.return_value = mock_bound_logger
        mock_bound_logger.bind.return_value = mock_bound_logger

        # Call middleware
        response = await middleware.dispatch(mock_request, call_next)

        # Check that logger was called with request context
        mock_logger.bind.assert_called_once()

        # Check that request was logged
        mock_bound_logger.info.assert_called()

        # Check that response headers were set
        assert "X-Process-Time" in response.headers
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] == mock_request.state.request_id

        # Check that metrics were recorded
        assert mock_record_count.call_count == 2  # One for request, one for response
        assert mock_record_timing.call_count == 1  # One for request duration


@pytest.mark.asyncio
async def test_mask_sensitive_data():
    """Test that sensitive data is masked in request/response bodies."""
    # Create middleware
    middleware = LoggingMiddleware(None)

    # Test data with sensitive fields
    test_data = {
        "username": "testuser",
        "password": "secret123",
        "api_key": "abcdef123456",
        "nested": {
            "token": "jwt123",
            "safe": "not-sensitive"
        },
        "list_data": [
            {"password": "secret456"},
            {"safe": "not-sensitive"}
        ]
    }

    # Mask sensitive data
    masked_data = middleware._mask_sensitive_data(test_data)

    # Check that sensitive fields are masked
    assert masked_data["username"] == "testuser"
    assert masked_data["password"] == "***MASKED***"
    assert masked_data["api_key"] == "***MASKED***"
    assert masked_data["nested"]["token"] == "***MASKED***"
    assert masked_data["nested"]["safe"] == "not-sensitive"
    assert masked_data["list_data"][0]["password"] == "***MASKED***"
    assert masked_data["list_data"][1]["safe"] == "not-sensitive"


@pytest.mark.asyncio
async def test_get_request_body(mock_request):
    """Test that request body is retrieved and masked correctly."""
    # Create middleware
    middleware = LoggingMiddleware(None)

    # Set up mock request with JSON body
    mock_request.headers = {"content-type": "application/json"}
    mock_request.body = AsyncMock(return_value=b'{"username": "testuser", "password": "secret123"}')

    # Get request body
    body = await middleware._get_request_body(mock_request)

    # Check that body was retrieved and sensitive data was masked
    assert body["username"] == "testuser"
    assert body["password"] == "***MASKED***"

    # Test with non-JSON content type
    mock_request.headers = {"content-type": "text/plain"}
    body = await middleware._get_request_body(mock_request)

    # Check that body is None for non-JSON content
    assert body is None

    # Test with invalid JSON
    mock_request.headers = {"content-type": "application/json"}
    mock_request.body = AsyncMock(return_value=b'invalid json')
    body = await middleware._get_request_body(mock_request)

    # Check that error is handled
    assert body["message"] == "Invalid JSON body"


@pytest.mark.asyncio
async def test_logging_middleware_exception(mock_request):
    """Test that LoggingMiddleware logs failed requests."""
    # Create a mock call_next function that raises an exception
    exception = ValueError("Test exception")
    call_next = AsyncMock(side_effect=exception)

    # Set up mock request
    mock_request.headers = {"content-type": "application/json"}
    mock_request.body = AsyncMock(return_value=b'{"test": "data"}')

    # Create middleware
    middleware = LoggingMiddleware(None)

    # Mock logger and metrics
    with patch("app.core.middleware.logging_middleware.logger") as mock_logger, \
         patch("app.core.middleware.logging_middleware.record_count") as mock_record_count:

        # Create mock bound logger
        mock_bound_logger = MagicMock()
        mock_logger.bind.return_value = mock_bound_logger
        mock_bound_logger.bind.return_value = mock_bound_logger

        # Call middleware and expect exception
        with pytest.raises(ValueError):
            await middleware.dispatch(mock_request, call_next)

        # Check that logger was called with request context
        mock_logger.bind.assert_called_once()

        # Check that exception was logged
        mock_bound_logger.exception.assert_called_once()

        # Check that error metric was recorded
        mock_record_count.assert_called_with(
            name="http_errors_total",
            tags={
                "method": mock_request.method,
                "path": mock_request.url.path,
                "error": "ValueError",
            }
        )
