"""
Tests for the performance profiling system.
"""

import time
from unittest.mock import patch, MagicMock

import pytest
from fastapi import Request, Response

from app.core.monitoring.profiling import (
    PerformanceCategory,
    PerformanceProfiler,
    profile,
    profile_function,
    record_api_request,
    record_db_query,
    record_llm_request,
    record_cache_operation,
    get_slow_operations,
    get_performance_summary,
)


def test_performance_profiler_initialization():
    """Test performance profiler initialization."""
    profiler = PerformanceProfiler(enabled=True)
    assert profiler.enabled is True

    profiler = PerformanceProfiler(enabled=False)
    assert profiler.enabled is False


def test_profile_context_manager():
    """Test profile context manager."""
    with patch('app.core.monitoring.profiling.PerformanceProfiler._record_timing') as mock_record:
        profiler = PerformanceProfiler(enabled=True)

        with profiler.profile("test_operation", PerformanceCategory.API):
            # Simulate some work
            time.sleep(0.01)

        # Check that record_timing was called
        assert mock_record.called


def test_profile_function_decorator():
    """Test profile function decorator."""
    with patch('app.core.monitoring.profiling.PerformanceProfiler._record_timing') as mock_record:
        profiler = PerformanceProfiler(enabled=True)

        @profiler.profile_function(PerformanceCategory.API)
        def test_function():
            # Simulate some work
            time.sleep(0.01)
            return "test"

        # Call the decorated function
        result = test_function()

        # Check that record_timing was called
        assert mock_record.called

        # Check that the function returned the correct result
        assert result == "test"


def test_record_api_request():
    """Test record_api_request function."""
    with patch('app.core.monitoring.profiling.record_timing') as mock_record:
        profiler = PerformanceProfiler(enabled=True)

        # Create mock request and response
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        # Record API request
        profiler.record_api_request(
            request=mock_request,
            response=mock_response,
            duration_ms=100.0,
            endpoint="/api/test",
        )

        # Check that record_timing was called
        assert mock_record.called


def test_record_db_query():
    """Test record_db_query function."""
    with patch('app.core.monitoring.profiling.record_timing') as mock_record:
        profiler = PerformanceProfiler(enabled=True)

        # Record database query
        profiler.record_db_query(
            query="SELECT * FROM users",
            duration_ms=50.0,
            params="user_id=1",
        )

        # Check that record_timing was called
        assert mock_record.called


def test_record_llm_request():
    """Test record_llm_request function."""
    with patch('app.core.monitoring.profiling.record_timing') as mock_record:
        profiler = PerformanceProfiler(enabled=True)

        # Record LLM request
        profiler.record_llm_request(
            model="gpt-4.1",
            prompt_tokens=100,
            completion_tokens=50,
            duration_ms=500.0,
            template_name="documentation_query",
        )

        # Check that record_timing was called
        assert mock_record.called


def test_record_cache_operation():
    """Test record_cache_operation function."""
    with patch('app.core.monitoring.profiling.record_timing') as mock_record:
        profiler = PerformanceProfiler(enabled=True)

        # Record cache operation
        profiler.record_cache_operation(
            operation="get",
            key="test:key",
            duration_ms=5.0,
            hit=True,
        )

        # Check that record_timing was called
        assert mock_record.called


def test_get_slow_operations():
    """Test get_slow_operations function."""
    with patch('app.core.monitoring.profiling.metrics_collector.get_metrics') as mock_get_metrics:
        # Create mock metrics
        from app.core.monitoring.metrics import PerformanceMetric

        mock_metrics = [
            PerformanceMetric(
                name="slow_operation",
                value=1000.0,
                timestamp=time.time(),
                tags={"category": PerformanceCategory.API},
            ),
            PerformanceMetric(
                name="fast_operation",
                value=10.0,
                timestamp=time.time(),
                tags={"category": PerformanceCategory.API},
            ),
        ]

        mock_get_metrics.return_value = mock_metrics

        profiler = PerformanceProfiler(enabled=True)

        # Get slow operations
        slow_ops = profiler.get_slow_operations(limit=1)

        # Check that we got the slow operation
        assert len(slow_ops) == 1
        assert slow_ops[0]["name"] == f"{PerformanceCategory.API}.slow_operation"
        assert slow_ops[0]["avg_ms"] == 1000.0


def test_get_performance_summary():
    """Test get_performance_summary function."""
    with patch('app.core.monitoring.profiling.metrics_collector.get_metrics') as mock_get_metrics:
        # Create mock metrics
        from app.core.monitoring.metrics import PerformanceMetric

        mock_metrics = [
            PerformanceMetric(
                name="api_operation",
                value=100.0,
                timestamp=time.time(),
                tags={"category": PerformanceCategory.API},
            ),
            PerformanceMetric(
                name="db_operation",
                value=50.0,
                timestamp=time.time(),
                tags={"category": PerformanceCategory.DATABASE},
            ),
        ]

        mock_get_metrics.return_value = mock_metrics

        profiler = PerformanceProfiler(enabled=True)

        # Get performance summary
        summary = profiler.get_performance_summary()

        # Check that we got the summary
        assert summary["enabled"] is True
        assert PerformanceCategory.API in summary["categories"]
        assert PerformanceCategory.DATABASE in summary["categories"]
        assert summary["categories"][PerformanceCategory.API]["avg_ms"] == 100.0
        assert summary["categories"][PerformanceCategory.DATABASE]["avg_ms"] == 50.0
