"""
Performance profiling system for the MAGPIE platform.

This module provides functionality for profiling and analyzing performance
of various components of the platform, including API endpoints, database queries,
and LLM API calls.
"""

import logging
import time
import functools
import statistics
from typing import Dict, List, Optional, Any, Callable, Union, TypeVar, cast
from datetime import datetime, timezone
from contextlib import contextmanager

from fastapi import Request, Response
from sqlalchemy.engine import Engine
from sqlalchemy import event

from app.core.config import settings, EnvironmentType
from app.core.monitoring.metrics import (
    PerformanceMetric,
    metrics_collector,
    record_timing,
    record_count
)
from app.core.monitoring.tracing import get_tracer, create_span
from app.core.cache.connection import RedisCache

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for generic type hints
F = TypeVar('F', bound=Callable[..., Any])
AsyncF = TypeVar('AsyncF', bound=Callable[..., Any])


class PerformanceCategory:
    """Performance metric categories."""

    API = "api"
    DATABASE = "database"
    LLM = "llm"
    CACHE = "cache"
    AGENT = "agent"
    ORCHESTRATOR = "orchestrator"
    DOCUMENTATION = "documentation"
    TROUBLESHOOTING = "troubleshooting"
    MAINTENANCE = "maintenance"


class PerformanceProfiler:
    """
    Performance profiler for the MAGPIE platform.

    This class provides methods for profiling and analyzing performance
    of various components of the platform.
    """

    def __init__(
        self,
        enabled: bool = True,
        redis_prefix: str = "profiling",
        redis_ttl: int = 86400 * 7,  # 7 days
    ):
        """
        Initialize performance profiler.

        Args:
            enabled: Whether profiling is enabled
            redis_prefix: Redis key prefix
            redis_ttl: Redis TTL in seconds
        """
        self.enabled = enabled and settings.ENVIRONMENT != EnvironmentType.TESTING
        self.redis_prefix = redis_prefix
        self.redis_ttl = redis_ttl
        self.logger = logger

        # Initialize Redis cache if not in testing mode
        if self.enabled:
            try:
                self.redis = RedisCache(prefix=redis_prefix)
            except Exception as e:
                self.logger.warning(f"Failed to initialize Redis for profiling: {e}")
                self.enabled = False

        # Initialize SQL query profiling if enabled
        if self.enabled and settings.PROFILE_SQL_QUERIES:
            try:
                from app.core.db.connection import engine
                self._setup_sql_query_profiling(engine)
                self.logger.info("SQL query profiling initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize SQL query profiling: {e}")

    def _setup_sql_query_profiling(self, engine: Engine) -> None:
        """
        Set up SQL query profiling.

        Args:
            engine: SQLAlchemy engine
        """
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            conn.info.setdefault('query_start_time', []).append(time.time())

        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            start_time = conn.info['query_start_time'].pop()
            total_time = (time.time() - start_time) * 1000  # Convert to ms

            # Record query timing
            self.record_db_query(
                query=statement[:100],  # Truncate long queries
                duration_ms=total_time,
                params=str(parameters)[:100] if parameters else None,  # Truncate long params
            )

    @contextmanager
    def profile(
        self,
        name: str,
        category: str = PerformanceCategory.API,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Context manager for profiling code execution.

        Args:
            name: Name of the operation
            category: Performance category
            tags: Additional tags

        Yields:
            None
        """
        if not self.enabled:
            yield
            return

        # Create tags
        tags = tags or {}
        tags["category"] = category

        # Record start time
        start_time = time.time()

        # Create span for tracing
        with create_span(
            name=f"{category}.{name}",
            attributes=tags,
        ):
            try:
                # Yield control
                yield
            finally:
                # Record timing
                duration_ms = (time.time() - start_time) * 1000
                self._record_timing(name, duration_ms, tags)

    async def profile_async(
        self,
        name: str,
        category: str = PerformanceCategory.API,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Async context manager for profiling async code execution.

        Args:
            name: Name of the operation
            category: Performance category
            tags: Additional tags

        Yields:
            None
        """
        if not self.enabled:
            yield
            return

        # Create tags
        tags = tags or {}
        tags["category"] = category

        # Record start time
        start_time = time.time()

        # Create span for tracing
        with create_span(
            name=f"{category}.{name}",
            attributes=tags,
        ):
            try:
                # Yield control
                yield
            finally:
                # Record timing
                duration_ms = (time.time() - start_time) * 1000
                self._record_timing(name, duration_ms, tags)

    def profile_function(
        self,
        category: str = PerformanceCategory.API,
        tags: Optional[Dict[str, str]] = None,
    ) -> Callable[[F], F]:
        """
        Decorator for profiling function execution.

        Args:
            category: Performance category
            tags: Additional tags

        Returns:
            Decorated function
        """
        def decorator(func: F) -> F:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with self.profile(func.__name__, category, tags):
                    return func(*args, **kwargs)
            return cast(F, wrapper)
        return decorator

    def profile_async_function(
        self,
        category: str = PerformanceCategory.API,
        tags: Optional[Dict[str, str]] = None,
    ) -> Callable[[AsyncF], AsyncF]:
        """
        Decorator for profiling async function execution.

        Args:
            category: Performance category
            tags: Additional tags

        Returns:
            Decorated function
        """
        def decorator(func: AsyncF) -> AsyncF:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                async with self.profile_async(func.__name__, category, tags):
                    return await func(*args, **kwargs)
            return cast(AsyncF, wrapper)
        return decorator

    def _record_timing(
        self,
        name: str,
        duration_ms: float,
        tags: Dict[str, str],
    ) -> None:
        """
        Record timing metric.

        Args:
            name: Name of the operation
            duration_ms: Duration in milliseconds
            tags: Additional tags
        """
        # Record in metrics collector
        record_timing(
            name=f"{tags.get('category', 'unknown')}.{name}",
            start_time=time.time() - (duration_ms / 1000),
            tags=tags,
        )

        # Log slow operations
        threshold_ms = self._get_threshold_for_category(tags.get('category', 'unknown'))
        if duration_ms > threshold_ms:
            self.logger.warning(
                f"Slow operation detected: {name} took {duration_ms:.2f}ms "
                f"(threshold: {threshold_ms}ms)",
                operation=name,
                duration_ms=duration_ms,
                threshold_ms=threshold_ms,
                tags=tags,
            )

    def _get_threshold_for_category(self, category: str) -> float:
        """
        Get threshold for slow operation detection.

        Args:
            category: Performance category

        Returns:
            float: Threshold in milliseconds
        """
        # Default thresholds by category
        thresholds = {
            PerformanceCategory.API: 500,  # 500ms for API endpoints
            PerformanceCategory.DATABASE: 100,  # 100ms for database queries
            PerformanceCategory.LLM: 2000,  # 2s for LLM API calls
            PerformanceCategory.CACHE: 50,  # 50ms for cache operations
            PerformanceCategory.AGENT: 1000,  # 1s for agent operations
            PerformanceCategory.ORCHESTRATOR: 800,  # 800ms for orchestrator operations
            PerformanceCategory.DOCUMENTATION: 1500,  # 1.5s for documentation operations
            PerformanceCategory.TROUBLESHOOTING: 1500,  # 1.5s for troubleshooting operations
            PerformanceCategory.MAINTENANCE: 1500,  # 1.5s for maintenance operations
        }

        return thresholds.get(category, 500)  # Default to 500ms

    def record_api_request(
        self,
        request: Request,
        response: Response,
        duration_ms: float,
        endpoint: str,
    ) -> None:
        """
        Record API request metric.

        Args:
            request: FastAPI request
            response: FastAPI response
            duration_ms: Duration in milliseconds
            endpoint: API endpoint
        """
        if not self.enabled:
            return

        # Create tags
        tags = {
            "category": PerformanceCategory.API,
            "method": request.method,
            "endpoint": endpoint,
            "status_code": str(response.status_code),
            "client_ip": request.client.host if request.client else "unknown",
        }

        # Record timing
        self._record_timing("api_request", duration_ms, tags)

        # Record count
        record_count(
            name="api_requests_total",
            value=1,
            tags=tags,
        )

    def record_db_query(
        self,
        query: str,
        duration_ms: float,
        params: Optional[str] = None,
    ) -> None:
        """
        Record database query metric.

        Args:
            query: SQL query
            duration_ms: Duration in milliseconds
            params: Query parameters
        """
        if not self.enabled:
            return

        # Create tags
        tags = {
            "category": PerformanceCategory.DATABASE,
            "query": query,
        }

        if params:
            tags["params"] = params

        # Record timing
        self._record_timing("db_query", duration_ms, tags)

        # Record count
        record_count(
            name="db_queries_total",
            value=1,
            tags=tags,
        )

    def record_llm_request(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: float,
        template_name: Optional[str] = None,
    ) -> None:
        """
        Record LLM request metric.

        Args:
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            duration_ms: Duration in milliseconds
            template_name: Prompt template name
        """
        if not self.enabled:
            return

        # Create tags
        tags = {
            "category": PerformanceCategory.LLM,
            "model": model,
            "prompt_tokens": str(prompt_tokens),
            "completion_tokens": str(completion_tokens),
            "total_tokens": str(prompt_tokens + completion_tokens),
        }

        if template_name:
            tags["template_name"] = template_name

        # Record timing
        self._record_timing("llm_request", duration_ms, tags)

        # Record count
        record_count(
            name="llm_requests_total",
            value=1,
            tags=tags,
        )

        # Record token usage
        record_count(
            name="llm_prompt_tokens_total",
            value=prompt_tokens,
            tags=tags,
        )

        record_count(
            name="llm_completion_tokens_total",
            value=completion_tokens,
            tags=tags,
        )

    def record_cache_operation(
        self,
        operation: str,
        key: str,
        duration_ms: float,
        hit: Optional[bool] = None,
    ) -> None:
        """
        Record cache operation metric.

        Args:
            operation: Cache operation (get, set, delete, etc.)
            key: Cache key
            duration_ms: Duration in milliseconds
            hit: Whether the operation was a cache hit (for get operations)
        """
        if not self.enabled:
            return

        # Create tags
        tags = {
            "category": PerformanceCategory.CACHE,
            "operation": operation,
            "key_prefix": key.split(":")[0] if ":" in key else "unknown",
        }

        if hit is not None:
            tags["hit"] = str(hit).lower()

        # Record timing
        self._record_timing("cache_operation", duration_ms, tags)

        # Record count
        record_count(
            name="cache_operations_total",
            value=1,
            tags=tags,
        )

        # Record cache hit/miss
        if hit is not None:
            record_count(
                name="cache_hits_total" if hit else "cache_misses_total",
                value=1,
                tags=tags,
            )

    def get_slow_operations(
        self,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get slow operations.

        Args:
            category: Filter by category
            limit: Maximum number of operations to return

        Returns:
            List of slow operations
        """
        if not self.enabled:
            return []

        try:
            # Get metrics
            metrics = metrics_collector.get_metrics()

            # Filter by category
            if category:
                metrics = [m for m in metrics if m.tags.get("category") == category]

            # Group by operation name
            operations = {}
            for metric in metrics:
                name = f"{metric.tags.get('category', 'unknown')}.{metric.name}"

                if name not in operations:
                    operations[name] = []

                operations[name].append(metric.value)

            # Calculate statistics
            stats = []
            for name, values in operations.items():
                if not values:
                    continue

                # Calculate statistics
                avg = statistics.mean(values)
                p95 = statistics.quantile(values, 0.95) if len(values) >= 20 else max(values)
                p99 = statistics.quantile(values, 0.99) if len(values) >= 100 else max(values)

                # Get threshold
                category = name.split(".")[0]
                threshold = self._get_threshold_for_category(category)

                # Check if slow
                if avg > threshold or p95 > threshold * 2:
                    stats.append({
                        "name": name,
                        "count": len(values),
                        "avg_ms": avg,
                        "p95_ms": p95,
                        "p99_ms": p99,
                        "max_ms": max(values),
                        "threshold_ms": threshold,
                    })

            # Sort by average time (descending)
            stats.sort(key=lambda x: x["avg_ms"], reverse=True)

            # Return top N
            return stats[:limit]
        except Exception as e:
            self.logger.error(f"Failed to get slow operations: {e}")
            return []

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary.

        Returns:
            Performance summary
        """
        if not self.enabled:
            return {
                "enabled": False,
                "message": "Performance profiling is disabled",
            }

        try:
            # Get metrics
            metrics = metrics_collector.get_metrics()

            # Group by category
            categories = {}
            for metric in metrics:
                category = metric.tags.get("category", "unknown")

                if category not in categories:
                    categories[category] = []

                categories[category].append(metric.value)

            # Calculate statistics
            stats = {}
            for category, values in categories.items():
                if not values:
                    continue

                # Calculate statistics
                stats[category] = {
                    "count": len(values),
                    "avg_ms": statistics.mean(values),
                    "p95_ms": statistics.quantile(values, 0.95) if len(values) >= 20 else max(values),
                    "p99_ms": statistics.quantile(values, 0.99) if len(values) >= 100 else max(values),
                    "max_ms": max(values),
                    "min_ms": min(values),
                }

            # Get slow operations
            slow_operations = self.get_slow_operations(limit=5)

            return {
                "enabled": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "categories": stats,
                "slow_operations": slow_operations,
            }
        except Exception as e:
            self.logger.error(f"Failed to get performance summary: {e}")
            return {
                "enabled": True,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


# Create a global profiler instance
profiler = PerformanceProfiler(
    enabled=settings.PERFORMANCE_PROFILING_ENABLED,
)


def profile(
    name: str,
    category: str = PerformanceCategory.API,
    tags: Optional[Dict[str, str]] = None,
):
    """
    Context manager for profiling code execution.

    Args:
        name: Name of the operation
        category: Performance category
        tags: Additional tags

    Returns:
        Context manager
    """
    return profiler.profile(name, category, tags)


async def profile_async(
    name: str,
    category: str = PerformanceCategory.API,
    tags: Optional[Dict[str, str]] = None,
):
    """
    Async context manager for profiling async code execution.

    Args:
        name: Name of the operation
        category: Performance category
        tags: Additional tags

    Returns:
        Async context manager
    """
    return profiler.profile_async(name, category, tags)


def profile_function(
    category: str = PerformanceCategory.API,
    tags: Optional[Dict[str, str]] = None,
) -> Callable[[F], F]:
    """
    Decorator for profiling function execution.

    Args:
        category: Performance category
        tags: Additional tags

    Returns:
        Decorated function
    """
    return profiler.profile_function(category, tags)


def profile_async_function(
    category: str = PerformanceCategory.API,
    tags: Optional[Dict[str, str]] = None,
) -> Callable[[AsyncF], AsyncF]:
    """
    Decorator for profiling async function execution.

    Args:
        category: Performance category
        tags: Additional tags

    Returns:
        Decorated function
    """
    return profiler.profile_async_function(category, tags)


def record_api_request(
    request: Request,
    response: Response,
    duration_ms: float,
    endpoint: str,
) -> None:
    """
    Record API request metric.

    Args:
        request: FastAPI request
        response: FastAPI response
        duration_ms: Duration in milliseconds
        endpoint: API endpoint
    """
    profiler.record_api_request(request, response, duration_ms, endpoint)


def record_db_query(
    query: str,
    duration_ms: float,
    params: Optional[str] = None,
) -> None:
    """
    Record database query metric.

    Args:
        query: SQL query
        duration_ms: Duration in milliseconds
        params: Query parameters
    """
    profiler.record_db_query(query, duration_ms, params)


def record_llm_request(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    duration_ms: float,
    template_name: Optional[str] = None,
) -> None:
    """
    Record LLM request metric.

    Args:
        model: Model name
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        duration_ms: Duration in milliseconds
        template_name: Prompt template name
    """
    profiler.record_llm_request(
        model, prompt_tokens, completion_tokens, duration_ms, template_name
    )


def record_cache_operation(
    operation: str,
    key: str,
    duration_ms: float,
    hit: Optional[bool] = None,
) -> None:
    """
    Record cache operation metric.

    Args:
        operation: Cache operation (get, set, delete, etc.)
        key: Cache key
        duration_ms: Duration in milliseconds
        hit: Whether the operation was a cache hit (for get operations)
    """
    profiler.record_cache_operation(operation, key, duration_ms, hit)


def get_slow_operations(
    category: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Get slow operations.

    Args:
        category: Filter by category
        limit: Maximum number of operations to return

    Returns:
        List of slow operations
    """
    return profiler.get_slow_operations(category, limit)


def get_performance_summary() -> Dict[str, Any]:
    """
    Get performance summary.

    Returns:
        Performance summary
    """
    return profiler.get_performance_summary()
