"""
Monitoring package for the MAGPIE platform.

This package provides functionality for monitoring, metrics collection,
error tracking, and alerting.
"""

from app.core.monitoring.metrics import (
    PerformanceMetric,
    MetricsCollector,
    metrics_collector,
    record_timing,
    record_count,
    get_metrics,
)

from app.core.monitoring.error_tracking import (
    ErrorSeverity,
    ErrorCategory,
    ErrorEvent,
    AlertConfig,
    ErrorTracker,
    error_tracker,
    track_error,
    resolve_error,
    get_errors,
    get_error_count,
    get_error_rate,
    register_notification_handler,
)

from app.core.monitoring.notifications import (
    EmailConfig,
    WebhookConfig,
    NotificationService,
    notification_service,
)

from app.core.monitoring.exception_handlers import (
    handle_exceptions,
)

from app.core.monitoring.analytics import (
    ModelSize,
    ModelPricing,
    UsageRecord,
    AnalyticsPeriod,
    UsageAnalytics,
    analytics_service,
    record_usage,
    get_user_metrics,
    get_model_metrics,
    get_agent_metrics,
    get_global_metrics,
    get_usage_records,
)

from app.core.monitoring.tracing import (
    TracingConfig,
    get_tracer_provider,
    get_tracer,
    create_span,
    trace_function,
    TracingMiddleware,
    setup_tracing,
    extract_trace_context,
    inject_trace_context,
)

from app.core.monitoring.log_management import (
    LogLevel,
    LogRetentionPolicy,
    AuditLogEvent,
    AuditLogRecord,
    LogManager,
    log_manager,
    record_audit_log,
    get_audit_logs,
    verify_audit_logs,
    rotate_logs,
)

from app.core.monitoring.profiling import (
    PerformanceCategory,
    PerformanceProfiler,
    profiler,
    profile,
    profile_async,
    profile_function,
    profile_async_function,
    record_api_request,
    record_db_query,
    record_llm_request,
    record_cache_operation,
    get_slow_operations,
    get_performance_summary,
)

__all__ = [
    # Metrics
    "PerformanceMetric",
    "MetricsCollector",
    "metrics_collector",
    "record_timing",
    "record_count",
    "get_metrics",

    # Error tracking
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorEvent",
    "AlertConfig",
    "ErrorTracker",
    "error_tracker",
    "track_error",
    "resolve_error",
    "get_errors",
    "get_error_count",
    "get_error_rate",
    "register_notification_handler",

    # Notifications
    "EmailConfig",
    "WebhookConfig",
    "NotificationService",
    "notification_service",

    # Exception handlers
    "handle_exceptions",

    # Analytics
    "ModelSize",
    "ModelPricing",
    "UsageRecord",
    "AnalyticsPeriod",
    "UsageAnalytics",
    "analytics_service",
    "record_usage",
    "get_user_metrics",
    "get_model_metrics",
    "get_agent_metrics",
    "get_global_metrics",
    "get_usage_records",

    # Tracing
    "TracingConfig",
    "get_tracer_provider",
    "get_tracer",
    "create_span",
    "trace_function",
    "TracingMiddleware",
    "setup_tracing",
    "extract_trace_context",
    "inject_trace_context",

    # Log management
    "LogLevel",
    "LogRetentionPolicy",
    "AuditLogEvent",
    "AuditLogRecord",
    "LogManager",
    "log_manager",
    "record_audit_log",
    "get_audit_logs",
    "verify_audit_logs",
    "rotate_logs",

    # Profiling
    "PerformanceCategory",
    "PerformanceProfiler",
    "profiler",
    "profile",
    "profile_async",
    "profile_function",
    "profile_async_function",
    "record_api_request",
    "record_db_query",
    "record_llm_request",
    "record_cache_operation",
    "get_slow_operations",
    "get_performance_summary",
]
