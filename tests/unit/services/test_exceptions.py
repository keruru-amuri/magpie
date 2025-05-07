"""Tests for exceptions module."""

import pytest

from app.services.exceptions import (
    AzureOpenAIError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
    InvalidRequestError,
    ModelNotFoundError,
    ContextLengthExceededError,
    ContentFilterError,
    map_openai_error,
)


class TestExceptions:
    """Tests for exceptions module."""

    def test_azure_openai_error(self):
        """Test AzureOpenAIError."""
        error = AzureOpenAIError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.status_code is None
        assert error.details == {}

        error = AzureOpenAIError("Test error", status_code=400, details={"key": "value"})
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.status_code == 400
        assert error.details == {"key": "value"}

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError()
        assert str(error) == "Authentication failed"
        assert error.status_code == 401

        error = AuthenticationError("Custom message")
        assert str(error) == "Custom message"
        assert error.status_code == 401

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError()
        assert str(error) == "Rate limit exceeded"
        assert error.status_code == 429

        error = RateLimitError("Custom message")
        assert str(error) == "Custom message"
        assert error.status_code == 429

    def test_service_unavailable_error(self):
        """Test ServiceUnavailableError."""
        error = ServiceUnavailableError()
        assert str(error) == "Service unavailable"
        assert error.status_code == 503

        error = ServiceUnavailableError("Custom message")
        assert str(error) == "Custom message"
        assert error.status_code == 503

    def test_invalid_request_error(self):
        """Test InvalidRequestError."""
        error = InvalidRequestError()
        assert str(error) == "Invalid request"
        assert error.status_code == 400

        error = InvalidRequestError("Custom message")
        assert str(error) == "Custom message"
        assert error.status_code == 400

    def test_model_not_found_error(self):
        """Test ModelNotFoundError."""
        error = ModelNotFoundError()
        assert str(error) == "Model not found"
        assert error.status_code == 404

        error = ModelNotFoundError("Custom message")
        assert str(error) == "Custom message"
        assert error.status_code == 404

    def test_context_length_exceeded_error(self):
        """Test ContextLengthExceededError."""
        error = ContextLengthExceededError()
        assert str(error) == "Context length exceeded"
        assert error.status_code == 400

        error = ContextLengthExceededError("Custom message")
        assert str(error) == "Custom message"
        assert error.status_code == 400

    def test_content_filter_error(self):
        """Test ContentFilterError."""
        error = ContentFilterError()
        assert str(error) == "Content filtered"
        assert error.status_code == 400

        error = ContentFilterError("Custom message")
        assert str(error) == "Custom message"
        assert error.status_code == 400

    def test_map_openai_error(self):
        """Test map_openai_error."""
        # Test authentication error
        error = Exception("Authentication failed")
        mapped_error = map_openai_error(error)
        assert isinstance(mapped_error, AuthenticationError)

        # Test rate limit error
        error = Exception("Rate limit exceeded")
        mapped_error = map_openai_error(error)
        assert isinstance(mapped_error, RateLimitError)

        # Test service unavailable error
        error = Exception("Service unavailable")
        mapped_error = map_openai_error(error)
        assert isinstance(mapped_error, ServiceUnavailableError)

        # Test invalid request error
        error = Exception("Invalid request")
        mapped_error = map_openai_error(error)
        assert isinstance(mapped_error, InvalidRequestError)

        # Test model not found error
        error = Exception("Model not found")
        mapped_error = map_openai_error(error)
        assert isinstance(mapped_error, ModelNotFoundError)

        # Test context length exceeded error
        error = Exception("Context length exceeded")
        mapped_error = map_openai_error(error)
        assert isinstance(mapped_error, ContextLengthExceededError)

        # Test content filter error
        error = Exception("Content filter")
        mapped_error = map_openai_error(error)
        assert isinstance(mapped_error, ContentFilterError)

        # Test unknown error
        error = Exception("Unknown error")
        mapped_error = map_openai_error(error)
        assert isinstance(mapped_error, AzureOpenAIError)
        assert str(mapped_error) == "Unknown error"
