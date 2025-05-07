"""
Test utilities for monitoring tests.

This module provides helper functions and mock implementations for testing
monitoring components.
"""

import contextlib
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


@contextlib.contextmanager
def isolated_tracer_provider():
    """
    Context manager that provides an isolated tracer provider for testing.

    This prevents tests from affecting each other's tracer providers and
    avoids the "Overriding of current TracerProvider is not allowed" error.

    Yields:
        tuple: (provider, exporter) where provider is the TracerProvider and
               exporter is a MagicMock that can be used to verify spans.
    """
    # Save the current tracer provider
    original_provider = trace.get_tracer_provider()

    # Create a new tracer provider with a mock exporter
    provider = TracerProvider()
    exporter = MagicMock()
    processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(processor)

    # Use a non-global approach to avoid the override error
    tracer = provider.get_tracer("test-tracer")

    try:
        # Yield the provider and exporter for the test to use
        yield provider, exporter, tracer
    finally:
        # Restore the original tracer provider
        if original_provider:
            # We don't actually set it back globally to avoid the override error
            pass


class MockRedis:
    """
    Mock Redis implementation for testing.

    This class provides a minimal implementation of Redis functionality
    for testing without requiring a real Redis server.
    """

    def __init__(self):
        """Initialize the mock Redis with an in-memory data store."""
        self.data = {}
        self.ttls = {}

    def set(self, key, value, ex=None):
        """Set a key-value pair with optional expiration."""
        # Store the key with the prefix to match how it's queried
        self.data[key] = value
        if ex is not None:
            self.ttls[key] = ex
        return True

    def get(self, key):
        """Get a value by key."""
        return self.data.get(key)

    def mget(self, keys):
        """Get multiple values by keys."""
        return [self.data.get(key) for key in keys]

    def keys(self, pattern):
        """Get keys matching a pattern."""
        # Simple pattern matching for testing
        if pattern.endswith('*'):
            prefix = pattern[:-1]
            return [k for k in self.data.keys() if k.startswith(prefix)]
        elif '*' in pattern:
            # Handle patterns like *audit:*
            parts = pattern.split('*')
            if len(parts) == 3 and parts[0] == '' and parts[2] == '':
                # Pattern is *middle*
                middle = parts[1]
                return [k for k in self.data.keys() if middle in k]
        return [k for k in self.data.keys() if k == pattern]

    def delete(self, key):
        """Delete a key."""
        if key in self.data:
            del self.data[key]
            if key in self.ttls:
                del self.ttls[key]
            return 1
        return 0


@contextlib.contextmanager
def mock_redis_cache():
    """
    Context manager that provides a mock Redis cache for testing.

    This prevents tests from trying to connect to a real Redis server.

    Yields:
        MockRedis: A mock Redis implementation.
    """
    mock_redis = MockRedis()

    # Create a mock Redis cache class
    mock_cache = MagicMock()
    mock_cache.redis = mock_redis

    # Patch the RedisCache class
    with patch('app.core.cache.connection.RedisCache') as mock_redis_cache_class:
        mock_redis_cache_class.return_value = mock_cache
        yield mock_redis
