"""Exceptions for Azure OpenAI service."""

from typing import Any, Dict, Optional


class AzureOpenAIError(Exception):
    """Base exception for Azure OpenAI service."""

    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.

        Args:
            message: Error message.
            status_code: HTTP status code.
            details: Additional error details.
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(AzureOpenAIError):
    """Exception for authentication errors."""

    def __init__(self, message: str = "Authentication failed", **kwargs: Any):
        """Initialize the exception."""
        super().__init__(message, status_code=401, **kwargs)


class RateLimitError(AzureOpenAIError):
    """Exception for rate limit errors."""

    def __init__(self, message: str = "Rate limit exceeded", **kwargs: Any):
        """Initialize the exception."""
        super().__init__(message, status_code=429, **kwargs)


class ServiceUnavailableError(AzureOpenAIError):
    """Exception for service unavailable errors."""

    def __init__(self, message: str = "Service unavailable", **kwargs: Any):
        """Initialize the exception."""
        super().__init__(message, status_code=503, **kwargs)


class InvalidRequestError(AzureOpenAIError):
    """Exception for invalid request errors."""

    def __init__(self, message: str = "Invalid request", **kwargs: Any):
        """Initialize the exception."""
        super().__init__(message, status_code=400, **kwargs)


class ModelNotFoundError(AzureOpenAIError):
    """Exception for model not found errors."""

    def __init__(self, message: str = "Model not found", **kwargs: Any):
        """Initialize the exception."""
        super().__init__(message, status_code=404, **kwargs)


class ContextLengthExceededError(AzureOpenAIError):
    """Exception for context length exceeded errors."""

    def __init__(self, message: str = "Context length exceeded", **kwargs: Any):
        """Initialize the exception."""
        super().__init__(message, status_code=400, **kwargs)


class ContentFilterError(AzureOpenAIError):
    """Exception for content filter errors."""

    def __init__(self, message: str = "Content filtered", **kwargs: Any):
        """Initialize the exception."""
        super().__init__(message, status_code=400, **kwargs)


def map_openai_error(error: Exception) -> AzureOpenAIError:
    """
    Map an OpenAI error to a custom exception.

    Args:
        error: OpenAI error.

    Returns:
        Custom exception.
    """
    error_str = str(error).lower()
    
    if "authentication" in error_str or "unauthorized" in error_str or "api key" in error_str:
        return AuthenticationError(str(error))
    elif "rate limit" in error_str or "too many requests" in error_str:
        return RateLimitError(str(error))
    elif "service unavailable" in error_str or "server error" in error_str:
        return ServiceUnavailableError(str(error))
    elif "invalid request" in error_str or "bad request" in error_str:
        return InvalidRequestError(str(error))
    elif "model not found" in error_str:
        return ModelNotFoundError(str(error))
    elif "context length" in error_str or "token limit" in error_str:
        return ContextLengthExceededError(str(error))
    elif "content filter" in error_str or "content policy" in error_str:
        return ContentFilterError(str(error))
    else:
        return AzureOpenAIError(str(error))
