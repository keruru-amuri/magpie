"""
Error tracking module for the MAGPIE platform.

This module provides functionality for tracking, categorizing, and alerting on errors.
"""

import json
import time
import traceback
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable

from loguru import logger
from pydantic import BaseModel, Field

from app.core.cache.connection import RedisCache
from app.core.config import settings
from app.core.monitoring.metrics import record_count


class ErrorSeverity(str, Enum):
    """
    Severity levels for errors.

    Attributes:
        DEBUG: Debug-level errors (lowest severity)
        INFO: Informational errors
        WARNING: Warning-level errors
        ERROR: Standard errors
        CRITICAL: Critical errors (highest severity)
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """
    Categories for errors.

    Attributes:
        SYSTEM: System-level errors (infrastructure, configuration)
        DATABASE: Database-related errors
        CACHE: Cache-related errors
        API: API-related errors
        AUTHENTICATION: Authentication and authorization errors
        VALIDATION: Input validation errors
        INTEGRATION: Integration with external systems
        LLM: Large Language Model errors
        BUSINESS_LOGIC: Business logic errors
        UNKNOWN: Unknown or uncategorized errors
    """

    SYSTEM = "system"
    DATABASE = "database"
    CACHE = "cache"
    API = "api"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    INTEGRATION = "integration"
    LLM = "llm"
    BUSINESS_LOGIC = "business_logic"
    UNKNOWN = "unknown"


class ErrorEvent(BaseModel):
    """
    Model for error events.

    Attributes:
        id: Unique identifier for the error
        message: Error message
        exception_type: Type of exception
        traceback: Exception traceback
        timestamp: Time when the error occurred
        severity: Severity level of the error
        category: Category of the error
        component: Component where the error occurred
        user_id: ID of the user who experienced the error (if applicable)
        request_id: ID of the request that caused the error (if applicable)
        context: Additional context for the error
        count: Number of occurrences of this error
        first_seen: Time when this error was first seen
        last_seen: Time when this error was last seen
        resolved: Whether the error has been resolved
        resolution_time: Time when the error was resolved
    """

    id: str
    message: str
    exception_type: str
    traceback: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    severity: ErrorSeverity = ErrorSeverity.ERROR
    category: ErrorCategory = ErrorCategory.UNKNOWN
    component: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    count: int = 1
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    resolution_time: Optional[datetime] = None


class AlertConfig(BaseModel):
    """
    Configuration for error alerts.

    Attributes:
        enabled: Whether alerts are enabled
        min_severity: Minimum severity level for alerts
        cooldown_minutes: Cooldown period between alerts for the same error
        rate_threshold: Number of errors per minute to trigger a rate alert
        rate_window_minutes: Time window for rate alerts
        notification_channels: Channels to use for notifications
    """

    enabled: bool = True
    min_severity: ErrorSeverity = ErrorSeverity.ERROR
    cooldown_minutes: int = 15
    rate_threshold: int = 10
    rate_window_minutes: int = 5
    notification_channels: List[str] = Field(default_factory=lambda: ["log"])


class ErrorTracker:
    """
    Tracker for error events.

    This class provides methods for tracking, categorizing, and alerting on errors.
    It uses Redis for storing error events.
    """

    def __init__(
        self,
        prefix: str = "errors",
        ttl: int = 604800,  # 7 days
        alert_config: Optional[AlertConfig] = None,
    ):
        """
        Initialize the error tracker.

        Args:
            prefix: Prefix for Redis keys
            ttl: Time-to-live for errors in seconds (default: 7 days)
            alert_config: Configuration for alerts
        """
        self.prefix = prefix
        self.ttl = ttl
        self.logger = logger.bind(name=__name__)
        self.alert_config = alert_config or AlertConfig()

        # Initialize notification handlers
        self.notification_handlers: Dict[str, Callable[[ErrorEvent], None]] = {
            "log": self._notify_log,
        }

        # Initialize Redis cache if not in testing mode
        if settings.ENVIRONMENT != "testing":
            try:
                self.redis = RedisCache(prefix=prefix)
                self.enabled = True
            except Exception as e:
                self.logger.warning(f"Failed to initialize Redis for error tracking: {e}")
                self.enabled = False
        else:
            self.enabled = False

    def track_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        component: str = "unknown",
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        alert: bool = True,
    ) -> Optional[ErrorEvent]:
        """
        Track an error event.

        Args:
            message: Error message
            exception: Exception object
            severity: Severity level of the error
            category: Category of the error
            component: Component where the error occurred
            user_id: ID of the user who experienced the error
            request_id: ID of the request that caused the error
            context: Additional context for the error
            alert: Whether to trigger alerts for this error

        Returns:
            Optional[ErrorEvent]: The error event, or None if tracking is disabled
        """
        if not self.enabled:
            # Log the error even if Redis is not available
            self._log_error(
                message, exception, severity, category, component, user_id, request_id, context
            )
            return None

        try:
            # Generate error ID based on exception type, message, and component
            exception_type = type(exception).__name__ if exception else "None"
            error_id = self._generate_error_id(exception_type, message, component)

            # Check if error already exists
            existing_error = self._get_error(error_id)

            if existing_error:
                # Update existing error
                existing_error.count += 1
                existing_error.last_seen = datetime.now(timezone.utc)

                # Update context if provided
                if context:
                    existing_error.context.update(context)

                # Store updated error
                self._store_error(existing_error)

                # Record metric
                self._record_error_metric(existing_error)

                # Check if alert should be triggered
                if alert and self._should_alert(existing_error):
                    self._send_alert(existing_error)

                return existing_error
            else:
                # Create new error event
                error_event = ErrorEvent(
                    id=error_id,
                    message=message,
                    exception_type=exception_type,
                    traceback=traceback.format_exc() if exception else None,
                    severity=severity,
                    category=category,
                    component=component,
                    user_id=user_id,
                    request_id=request_id,
                    context=context or {},
                )

                # Store error
                self._store_error(error_event)

                # Record metric
                self._record_error_metric(error_event)

                # Check if alert should be triggered
                if alert and self._should_alert(error_event):
                    self._send_alert(error_event)

                return error_event
        except Exception as e:
            # Log error if tracking fails
            self.logger.error(f"Failed to track error: {e}")
            self._log_error(
                message, exception, severity, category, component, user_id, request_id, context
            )
            return None

    def resolve_error(self, error_id: str) -> bool:
        """
        Mark an error as resolved.

        Args:
            error_id: ID of the error to resolve

        Returns:
            bool: True if the error was resolved, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Get error
            error = self._get_error(error_id)

            if not error:
                return False

            # Mark as resolved
            error.resolved = True
            error.resolution_time = datetime.now(timezone.utc)

            # Store updated error
            self._store_error(error)

            return True
        except Exception as e:
            self.logger.error(f"Failed to resolve error: {e}")
            return False

    def get_errors(
        self,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        component: Optional[str] = None,
        resolved: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[ErrorEvent]:
        """
        Get error events from Redis.

        Args:
            severity: Filter by severity level
            category: Filter by category
            component: Filter by component
            resolved: Filter by resolution status
            start_time: Start time for filtering
            end_time: End time for filtering
            limit: Maximum number of errors to return

        Returns:
            List[ErrorEvent]: List of error events
        """
        if not self.enabled:
            return []

        try:
            # Create pattern for keys
            pattern = f"{self.prefix}:*"

            # Get keys matching the pattern
            keys = self.redis.redis.keys(pattern)

            # Sort keys by timestamp (embedded in the key)
            keys = sorted(keys, reverse=True)[:limit * 2]  # Get more than needed for filtering

            # Get values for keys
            if not keys:
                return []

            values = self.redis.redis.mget(keys)

            # Parse values into errors
            errors = []
            for value in values:
                if value:
                    try:
                        error_dict = json.loads(value.decode("utf-8"))
                        error = ErrorEvent.model_validate(error_dict)

                        # Apply filters
                        if severity and error.severity != severity:
                            continue
                        if category and error.category != category:
                            continue
                        if component and error.component != component:
                            continue
                        if resolved is not None and error.resolved != resolved:
                            continue
                        if start_time and error.timestamp < start_time:
                            continue
                        if end_time and error.timestamp > end_time:
                            continue

                        errors.append(error)

                        # Check limit after filtering
                        if len(errors) >= limit:
                            break
                    except Exception as e:
                        self.logger.error(f"Failed to parse error: {e}")

            return errors
        except Exception as e:
            self.logger.error(f"Failed to get errors: {e}")
            return []

    def get_error_count(
        self,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        component: Optional[str] = None,
        resolved: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """
        Get the count of error events.

        Args:
            severity: Filter by severity level
            category: Filter by category
            component: Filter by component
            resolved: Filter by resolution status
            start_time: Start time for filtering
            end_time: End time for filtering

        Returns:
            int: Count of error events
        """
        if not self.enabled:
            return 0

        try:
            # Create pattern for keys
            pattern = f"{self.prefix}:*"

            # Get keys matching the pattern
            keys = self.redis.redis.keys(pattern)

            # Get values for keys
            if not keys:
                return 0

            values = self.redis.redis.mget(keys)

            # Count errors matching filters
            count = 0
            for value in values:
                if value:
                    try:
                        error_dict = json.loads(value.decode("utf-8"))
                        error = ErrorEvent.model_validate(error_dict)

                        # Apply filters
                        if severity and error.severity != severity:
                            continue
                        if category and error.category != category:
                            continue
                        if component and error.component != component:
                            continue
                        if resolved is not None and error.resolved != resolved:
                            continue
                        if start_time and error.timestamp < start_time:
                            continue
                        if end_time and error.timestamp > end_time:
                            continue

                        count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to parse error: {e}")

            return count
        except Exception as e:
            self.logger.error(f"Failed to get error count: {e}")
            return 0

    def get_error_rate(
        self,
        window_minutes: int = 5,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        component: Optional[str] = None,
    ) -> float:
        """
        Get the error rate (errors per minute) for a time window.

        Args:
            window_minutes: Time window in minutes
            severity: Filter by severity level
            category: Filter by category
            component: Filter by component

        Returns:
            float: Error rate (errors per minute)
        """
        if not self.enabled:
            return 0.0

        try:
            # Calculate start time
            start_time = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

            # Get error count
            error_count = self.get_error_count(
                severity=severity,
                category=category,
                component=component,
                start_time=start_time,
            )

            # Calculate error rate
            if window_minutes > 0:
                error_rate = error_count / window_minutes
            else:
                error_rate = 0.0

            return error_rate
        except Exception as e:
            self.logger.error(f"Failed to get error rate: {e}")
            return 0.0

    def register_notification_handler(
        self, channel: str, handler: Callable[[ErrorEvent], None]
    ) -> None:
        """
        Register a notification handler for a channel.

        Args:
            channel: Channel name
            handler: Handler function
        """
        self.notification_handlers[channel] = handler

    def _generate_error_id(self, exception_type: str, message: str, component: str) -> str:
        """
        Generate a unique ID for an error.

        Args:
            exception_type: Type of exception
            message: Error message
            component: Component where the error occurred

        Returns:
            str: Unique error ID
        """
        # Use first 100 chars of message to avoid very long IDs
        message_part = message[:100].strip().lower()

        # Replace spaces and special characters
        message_part = message_part.replace(" ", "_").replace(":", "_").replace(".", "_")

        # Generate ID
        return f"{component}_{exception_type}_{message_part}"

    def _get_error(self, error_id: str) -> Optional[ErrorEvent]:
        """
        Get an error by ID.

        Args:
            error_id: Error ID

        Returns:
            Optional[ErrorEvent]: Error event, or None if not found
        """
        if not self.enabled:
            return None

        try:
            # Get error from Redis
            key = f"{self.prefix}:{error_id}"
            value = self.redis.redis.get(key)

            if not value:
                return None

            # Parse error
            error_dict = json.loads(value.decode("utf-8"))
            return ErrorEvent.model_validate(error_dict)
        except Exception as e:
            self.logger.error(f"Failed to get error: {e}")
            return None

    def _store_error(self, error: ErrorEvent) -> bool:
        """
        Store an error in Redis.

        Args:
            error: Error event

        Returns:
            bool: True if the error was stored, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Store error in Redis
            key = f"{self.prefix}:{error.id}"
            self.redis.redis.set(
                key,
                error.model_dump_json(),
                ex=self.ttl
            )

            return True
        except Exception as e:
            self.logger.error(f"Failed to store error: {e}")
            return False

    def _record_error_metric(self, error: ErrorEvent) -> None:
        """
        Record a metric for an error.

        Args:
            error: Error event
        """
        try:
            # Record count metric
            record_count(
                name="error_events_total",
                tags={
                    "severity": error.severity,
                    "category": error.category,
                    "component": error.component,
                    "exception_type": error.exception_type,
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to record error metric: {e}")

    def _should_alert(self, error: ErrorEvent) -> bool:
        """
        Check if an alert should be triggered for an error.

        Args:
            error: Error event

        Returns:
            bool: True if an alert should be triggered, False otherwise
        """
        if not self.alert_config.enabled:
            return False

        # Check severity
        severity_levels = list(ErrorSeverity)
        min_severity_index = severity_levels.index(self.alert_config.min_severity)
        error_severity_index = severity_levels.index(error.severity)

        if error_severity_index < min_severity_index:
            return False

        # Check cooldown
        if error.count > 1:
            last_seen = error.last_seen
            cooldown = timedelta(minutes=self.alert_config.cooldown_minutes)

            if datetime.now(timezone.utc) - last_seen < cooldown:
                return False

        # Check error rate
        if self.alert_config.rate_threshold > 0:
            error_rate = self.get_error_rate(
                window_minutes=self.alert_config.rate_window_minutes,
                severity=error.severity,
                category=error.category,
                component=error.component,
            )

            if error_rate >= self.alert_config.rate_threshold:
                return True

        # Alert on first occurrence or after cooldown
        return True

    def _send_alert(self, error: ErrorEvent) -> None:
        """
        Send an alert for an error.

        Args:
            error: Error event
        """
        try:
            # Send notifications to all configured channels
            for channel in self.alert_config.notification_channels:
                handler = self.notification_handlers.get(channel)

                if handler:
                    handler(error)
                else:
                    self.logger.warning(f"No handler for notification channel: {channel}")
        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}")

    def _notify_log(self, error: ErrorEvent) -> None:
        """
        Send a notification to the log.

        Args:
            error: Error event
        """
        log_message = (
            f"ALERT: {error.severity.upper()} error in {error.component}: "
            f"{error.exception_type}: {error.message}"
        )

        if error.count > 1:
            log_message += f" (occurred {error.count} times, last seen: {error.last_seen})"

        # Log at appropriate level
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error.severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif error.severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        elif error.severity == ErrorSeverity.INFO:
            self.logger.info(log_message)
        else:
            self.logger.debug(log_message)

    def _log_error(
        self,
        message: str,
        exception: Optional[Exception],
        severity: ErrorSeverity,
        category: ErrorCategory,
        component: str,
        user_id: Optional[str],
        request_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> None:
        """
        Log an error when Redis is not available.

        Args:
            message: Error message
            exception: Exception object
            severity: Severity level
            category: Error category
            component: Component where the error occurred
            user_id: User ID
            request_id: Request ID
            context: Additional context
        """
        log_context = {
            "severity": severity,
            "category": category,
            "component": component,
        }

        if user_id:
            log_context["user_id"] = user_id

        if request_id:
            log_context["request_id"] = request_id

        if context:
            log_context.update(context)

        if exception:
            if severity == ErrorSeverity.CRITICAL:
                self.logger.bind(**log_context).critical(f"{message}: {exception}")
            elif severity == ErrorSeverity.ERROR:
                self.logger.bind(**log_context).error(f"{message}: {exception}")
            elif severity == ErrorSeverity.WARNING:
                self.logger.bind(**log_context).warning(f"{message}: {exception}")
            elif severity == ErrorSeverity.INFO:
                self.logger.bind(**log_context).info(f"{message}: {exception}")
            else:
                self.logger.bind(**log_context).debug(f"{message}: {exception}")
        else:
            if severity == ErrorSeverity.CRITICAL:
                self.logger.bind(**log_context).critical(message)
            elif severity == ErrorSeverity.ERROR:
                self.logger.bind(**log_context).error(message)
            elif severity == ErrorSeverity.WARNING:
                self.logger.bind(**log_context).warning(message)
            elif severity == ErrorSeverity.INFO:
                self.logger.bind(**log_context).info(message)
            else:
                self.logger.bind(**log_context).debug(message)


# Create a global error tracker instance
error_tracker = ErrorTracker()


def track_error(
    message: str,
    exception: Optional[Exception] = None,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    component: str = "unknown",
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    alert: bool = True,
) -> Optional[ErrorEvent]:
    """
    Track an error event.

    Args:
        message: Error message
        exception: Exception object
        severity: Severity level of the error
        category: Category of the error
        component: Component where the error occurred
        user_id: ID of the user who experienced the error
        request_id: ID of the request that caused the error
        context: Additional context for the error
        alert: Whether to trigger alerts for this error

    Returns:
        Optional[ErrorEvent]: The error event, or None if tracking is disabled
    """
    return error_tracker.track_error(
        message=message,
        exception=exception,
        severity=severity,
        category=category,
        component=component,
        user_id=user_id,
        request_id=request_id,
        context=context,
        alert=alert
    )


def resolve_error(error_id: str) -> bool:
    """
    Mark an error as resolved.

    Args:
        error_id: ID of the error to resolve

    Returns:
        bool: True if the error was resolved, False otherwise
    """
    return error_tracker.resolve_error(error_id)


def get_errors(
    severity: Optional[ErrorSeverity] = None,
    category: Optional[ErrorCategory] = None,
    component: Optional[str] = None,
    resolved: Optional[bool] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
) -> List[ErrorEvent]:
    """
    Get error events.

    Args:
        severity: Filter by severity level
        category: Filter by category
        component: Filter by component
        resolved: Filter by resolution status
        start_time: Start time for filtering
        end_time: End time for filtering
        limit: Maximum number of errors to return

    Returns:
        List[ErrorEvent]: List of error events
    """
    return error_tracker.get_errors(
        severity, category, component, resolved, start_time, end_time, limit
    )


def get_error_count(
    severity: Optional[ErrorSeverity] = None,
    category: Optional[ErrorCategory] = None,
    component: Optional[str] = None,
    resolved: Optional[bool] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> int:
    """
    Get the count of error events.

    Args:
        severity: Filter by severity level
        category: Filter by category
        component: Filter by component
        resolved: Filter by resolution status
        start_time: Start time for filtering
        end_time: End time for filtering

    Returns:
        int: Count of error events
    """
    return error_tracker.get_error_count(
        severity, category, component, resolved, start_time, end_time
    )


def get_error_rate(
    window_minutes: int = 5,
    severity: Optional[ErrorSeverity] = None,
    category: Optional[ErrorCategory] = None,
    component: Optional[str] = None,
) -> float:
    """
    Get the error rate (errors per minute) for a time window.

    Args:
        window_minutes: Time window in minutes
        severity: Filter by severity level
        category: Filter by category
        component: Filter by component

    Returns:
        float: Error rate (errors per minute)
    """
    return error_tracker.get_error_rate(window_minutes, severity, category, component)


def register_notification_handler(
    channel: str, handler: Callable[[ErrorEvent], None]
) -> None:
    """
    Register a notification handler for a channel.

    Args:
        channel: Channel name
        handler: Handler function
    """
    error_tracker.register_notification_handler(channel, handler)
