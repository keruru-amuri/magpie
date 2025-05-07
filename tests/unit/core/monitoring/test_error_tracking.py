"""
Unit tests for error tracking module.
"""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.core.monitoring.error_tracking import (
    ErrorSeverity,
    ErrorCategory,
    ErrorEvent,
    AlertConfig,
    ErrorTracker,
    track_error,
    resolve_error,
    get_errors,
    get_error_count,
    get_error_rate,
)


def test_error_event_model():
    """Test that ErrorEvent model works correctly."""
    # Create an error event
    error = ErrorEvent(
        id="test_error_id",
        message="Test error message",
        exception_type="ValueError",
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
        user_id="test_user",
        request_id="test_request",
        context={"test_key": "test_value"},
    )

    # Check that the error has the expected values
    assert error.id == "test_error_id"
    assert error.message == "Test error message"
    assert error.exception_type == "ValueError"
    assert error.severity == ErrorSeverity.ERROR
    assert error.category == ErrorCategory.API
    assert error.component == "test_component"
    assert error.user_id == "test_user"
    assert error.request_id == "test_request"
    assert error.context == {"test_key": "test_value"}
    assert error.count == 1
    assert isinstance(error.timestamp, datetime)
    assert isinstance(error.first_seen, datetime)
    assert isinstance(error.last_seen, datetime)
    assert error.resolved is False
    assert error.resolution_time is None


def test_alert_config_model():
    """Test that AlertConfig model works correctly."""
    # Create an alert config
    config = AlertConfig(
        enabled=True,
        min_severity=ErrorSeverity.ERROR,
        cooldown_minutes=15,
        rate_threshold=10,
        rate_window_minutes=5,
        notification_channels=["email", "webhook"],
    )

    # Check that the config has the expected values
    assert config.enabled is True
    assert config.min_severity == ErrorSeverity.ERROR
    assert config.cooldown_minutes == 15
    assert config.rate_threshold == 10
    assert config.rate_window_minutes == 5
    assert config.notification_channels == ["email", "webhook"]


@patch("app.core.monitoring.error_tracking.RedisCache")
def test_error_tracker_init(mock_redis_cache):
    """Test that ErrorTracker initializes correctly."""
    # Create a tracker
    tracker = ErrorTracker(prefix="test_prefix", ttl=3600)

    # Check that the tracker has the expected values
    assert tracker.prefix == "test_prefix"
    assert tracker.ttl == 3600
    assert tracker.enabled is True

    # Check that Redis was initialized
    mock_redis_cache.assert_called_once_with(prefix="test_prefix")


@patch("app.core.monitoring.error_tracking.RedisCache")
def test_error_tracker_track_error_new(mock_redis_cache):
    """Test that ErrorTracker.track_error works correctly for new errors."""
    # Create a mock Redis instance
    mock_redis = MagicMock()
    mock_redis_cache.return_value.redis = mock_redis
    mock_redis.get.return_value = None

    # Create a tracker
    tracker = ErrorTracker(prefix="test_prefix", ttl=3600)

    # Track an error
    error = tracker.track_error(
        message="Test error message",
        exception=ValueError("Test error"),
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
        user_id="test_user",
        request_id="test_request",
        context={"test_key": "test_value"},
        alert=False,
    )

    # Check that the error was tracked
    assert error is not None
    assert error.message == "Test error message"
    assert error.exception_type == "ValueError"
    assert error.severity == ErrorSeverity.ERROR
    assert error.category == ErrorCategory.API
    assert error.component == "test_component"
    assert error.user_id == "test_user"
    assert error.request_id == "test_request"
    assert error.context == {"test_key": "test_value"}
    assert error.count == 1

    # Check that the error was stored in Redis
    mock_redis.set.assert_called_once()
    args, kwargs = mock_redis.set.call_args
    assert args[0].startswith("test_prefix:")
    assert "test_component" in args[0]
    assert "ValueError" in args[0]
    assert "test_error_message" in args[0]
    assert kwargs["ex"] == 3600


@patch("app.core.monitoring.error_tracking.RedisCache")
def test_error_tracker_track_error_existing(mock_redis_cache):
    """Test that ErrorTracker.track_error works correctly for existing errors."""
    # Create a mock Redis instance
    mock_redis = MagicMock()
    mock_redis_cache.return_value.redis = mock_redis

    # Create an existing error
    existing_error = ErrorEvent(
        id="test_component_ValueError_test_error_message",
        message="Test error message",
        exception_type="ValueError",
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
        user_id="test_user",
        request_id="test_request",
        context={"test_key": "test_value"},
        count=1,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc),
    )

    # Mock Redis.get to return the existing error
    mock_redis.get.return_value = existing_error.model_dump_json().encode("utf-8")

    # Create a tracker
    tracker = ErrorTracker(prefix="test_prefix", ttl=3600)

    # Track the same error again
    error = tracker.track_error(
        message="Test error message",
        exception=ValueError("Test error"),
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
        user_id="test_user",
        request_id="test_request",
        context={"new_key": "new_value"},
        alert=False,
    )

    # Check that the error was updated
    assert error is not None
    assert error.id == "test_component_ValueError_test_error_message"
    assert error.count == 2
    assert error.context == {"test_key": "test_value", "new_key": "new_value"}

    # Check that the error was stored in Redis
    mock_redis.set.assert_called_once()


@patch("app.core.monitoring.error_tracking.RedisCache")
def test_error_tracker_resolve_error(mock_redis_cache):
    """Test that ErrorTracker.resolve_error works correctly."""
    # Create a mock Redis instance
    mock_redis = MagicMock()
    mock_redis_cache.return_value.redis = mock_redis

    # Create an existing error
    existing_error = ErrorEvent(
        id="test_error_id",
        message="Test error message",
        exception_type="ValueError",
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
        user_id="test_user",
        request_id="test_request",
        context={"test_key": "test_value"},
        count=1,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc),
    )

    # Mock Redis.get to return the existing error
    mock_redis.get.return_value = existing_error.model_dump_json().encode("utf-8")

    # Create a tracker
    tracker = ErrorTracker(prefix="test_prefix", ttl=3600)

    # Resolve the error
    result = tracker.resolve_error("test_error_id")

    # Check that the error was resolved
    assert result is True

    # Check that the error was stored in Redis
    mock_redis.set.assert_called_once()
    args, kwargs = mock_redis.set.call_args
    assert args[0] == "test_prefix:test_error_id"

    # Parse the stored error
    stored_error = json.loads(args[1])
    assert stored_error["resolved"] is True
    assert stored_error["resolution_time"] is not None


@patch("app.core.monitoring.error_tracking.RedisCache")
def test_error_tracker_get_errors(mock_redis_cache):
    """Test that ErrorTracker.get_errors works correctly."""
    # Create a mock Redis instance
    mock_redis = MagicMock()
    mock_redis_cache.return_value.redis = mock_redis

    # Create mock errors
    error1 = ErrorEvent(
        id="test_error_id_1",
        message="Test error message 1",
        exception_type="ValueError",
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
        user_id="test_user",
        request_id="test_request",
        context={"test_key": "test_value"},
        count=1,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc),
    )

    error2 = ErrorEvent(
        id="test_error_id_2",
        message="Test error message 2",
        exception_type="TypeError",
        severity=ErrorSeverity.WARNING,
        category=ErrorCategory.DATABASE,
        component="test_component_2",
        user_id="test_user_2",
        request_id="test_request_2",
        context={"test_key_2": "test_value_2"},
        count=2,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc),
    )

    # Mock Redis.keys to return the error keys
    mock_redis.keys.return_value = [
        b"test_prefix:test_error_id_1",
        b"test_prefix:test_error_id_2",
    ]

    # Mock Redis.mget to return the error values
    mock_redis.mget.return_value = [
        error1.model_dump_json().encode("utf-8"),
        error2.model_dump_json().encode("utf-8"),
    ]

    # Create a tracker
    tracker = ErrorTracker(prefix="test_prefix", ttl=3600)

    # Get all errors
    errors = tracker.get_errors()

    # Check that the errors were retrieved
    assert len(errors) == 2
    assert errors[0].id == "test_error_id_1"
    assert errors[1].id == "test_error_id_2"

    # Get errors with filters
    errors = tracker.get_errors(
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
    )

    # Check that the errors were filtered
    assert len(errors) == 1
    assert errors[0].id == "test_error_id_1"


@patch("app.core.monitoring.error_tracking.error_tracker")
def test_track_error_function(mock_tracker):
    """Test that track_error function works correctly."""
    # Set up mock tracker
    mock_tracker.track_error.return_value = ErrorEvent(
        id="test_error_id",
        message="Test error message",
        exception_type="ValueError",
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
        user_id="test_user",
        request_id="test_request",
        context={"test_key": "test_value"},
    )

    # Track an error
    error = track_error(
        message="Test error message",
        exception=ValueError("Test error"),
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
        user_id="test_user",
        request_id="test_request",
        context={"test_key": "test_value"},
        alert=True,
    )

    # Check that the error was tracked
    assert error is not None
    assert error.id == "test_error_id"

    # Check that the tracker was called
    mock_tracker.track_error.assert_called_once()

    # Check the arguments individually since the order might be different
    args, kwargs = mock_tracker.track_error.call_args

    # Since we're using keyword arguments, all arguments should be in kwargs
    assert kwargs.get("message") == "Test error message"
    assert isinstance(kwargs.get("exception"), ValueError)
    assert kwargs.get("severity") == ErrorSeverity.ERROR
    assert kwargs.get("category") == ErrorCategory.API
    assert kwargs.get("component") == "test_component"
    assert kwargs.get("user_id") == "test_user"
    assert kwargs.get("request_id") == "test_request"
    assert kwargs.get("context") == {"test_key": "test_value"}
    assert kwargs.get("alert") is True


@patch("app.core.monitoring.error_tracking.error_tracker")
def test_resolve_error_function(mock_tracker):
    """Test that resolve_error function works correctly."""
    # Set up mock tracker
    mock_tracker.resolve_error.return_value = True

    # Resolve an error
    result = resolve_error("test_error_id")

    # Check that the error was resolved
    assert result is True

    # Check that the tracker was called
    mock_tracker.resolve_error.assert_called_once_with("test_error_id")


@patch("app.core.monitoring.error_tracking.error_tracker")
def test_get_errors_function(mock_tracker):
    """Test that get_errors function works correctly."""
    # Set up mock tracker
    mock_tracker.get_errors.return_value = [
        ErrorEvent(
            id="test_error_id",
            message="Test error message",
            exception_type="ValueError",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.API,
            component="test_component",
            user_id="test_user",
            request_id="test_request",
            context={"test_key": "test_value"},
        )
    ]

    # Get errors
    errors = get_errors(
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
        resolved=False,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        limit=10,
    )

    # Check that the errors were retrieved
    assert len(errors) == 1
    assert errors[0].id == "test_error_id"

    # Check that the tracker was called
    mock_tracker.get_errors.assert_called_once_with(
        ErrorSeverity.ERROR,
        ErrorCategory.API,
        "test_component",
        False,
        errors[0].timestamp,
        errors[0].timestamp,
        10,
    )


@patch("app.core.monitoring.error_tracking.error_tracker")
def test_get_error_count_function(mock_tracker):
    """Test that get_error_count function works correctly."""
    # Set up mock tracker
    mock_tracker.get_error_count.return_value = 5

    # Get error count
    count = get_error_count(
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
        resolved=False,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
    )

    # Check that the count was retrieved
    assert count == 5

    # Check that the tracker was called
    mock_tracker.get_error_count.assert_called_once()


@patch("app.core.monitoring.error_tracking.error_tracker")
def test_get_error_rate_function(mock_tracker):
    """Test that get_error_rate function works correctly."""
    # Set up mock tracker
    mock_tracker.get_error_rate.return_value = 2.5

    # Get error rate
    rate = get_error_rate(
        window_minutes=5,
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.API,
        component="test_component",
    )

    # Check that the rate was retrieved
    assert rate == 2.5

    # Check that the tracker was called
    mock_tracker.get_error_rate.assert_called_once_with(
        5,
        ErrorSeverity.ERROR,
        ErrorCategory.API,
        "test_component",
    )
