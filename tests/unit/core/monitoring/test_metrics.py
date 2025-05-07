"""
Unit tests for metrics module.
"""

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.core.monitoring.metrics import (
    PerformanceMetric,
    MetricsCollector,
    record_timing,
    record_count,
    get_metrics,
)


def test_performance_metric_model():
    """Test that PerformanceMetric model works correctly."""
    # Create a metric
    metric = PerformanceMetric(
        name="test_metric",
        value=123.45,
        unit="ms",
        tags={"tag1": "value1", "tag2": "value2"},
    )

    # Check that the metric has the expected values
    assert metric.name == "test_metric"
    assert metric.value == 123.45
    assert metric.unit == "ms"
    assert metric.tags == {"tag1": "value1", "tag2": "value2"}
    assert isinstance(metric.timestamp, datetime)


@patch("app.core.monitoring.metrics.RedisCache")
def test_metrics_collector_init(mock_redis_cache):
    """Test that MetricsCollector initializes correctly."""
    # Create a collector
    collector = MetricsCollector(prefix="test_prefix", ttl=3600)

    # Check that the collector has the expected values
    assert collector.prefix == "test_prefix"
    assert collector.ttl == 3600
    assert collector.enabled is True

    # Check that Redis was initialized
    mock_redis_cache.assert_called_once_with(prefix="test_prefix")


@patch("app.core.monitoring.metrics.RedisCache")
def test_metrics_collector_record_metric(mock_redis_cache):
    """Test that MetricsCollector.record_metric works correctly."""
    # Create a mock Redis instance
    mock_redis = MagicMock()
    mock_redis_cache.return_value.redis = mock_redis

    # Create a collector
    collector = MetricsCollector(prefix="test_prefix", ttl=3600)

    # Create a metric
    metric = PerformanceMetric(
        name="test_metric",
        value=123.45,
        unit="ms",
        tags={"tag1": "value1", "tag2": "value2"},
    )

    # Record the metric
    result = collector.record_metric(metric)

    # Check that the metric was recorded
    assert result is True
    mock_redis.set.assert_called_once()

    # Check that the key and value are correct
    args, kwargs = mock_redis.set.call_args
    assert args[0].startswith("test_prefix:test_metric:")
    assert "test_metric" in args[1]
    assert "123.45" in args[1]
    assert "ms" in args[1]
    assert kwargs["ex"] == 3600


@patch("app.core.monitoring.metrics.RedisCache")
def test_metrics_collector_record_timing(mock_redis_cache):
    """Test that MetricsCollector.record_timing works correctly."""
    # Create a mock Redis instance
    mock_redis = MagicMock()
    mock_redis_cache.return_value.redis = mock_redis

    # Create a collector
    collector = MetricsCollector(prefix="test_prefix", ttl=3600)

    # Record a timing metric
    start_time = time.time() - 1  # 1 second ago
    result = collector.record_timing(
        name="test_timing",
        start_time=start_time,
        tags={"tag1": "value1"},
    )

    # Check that the metric was recorded
    assert result is True
    mock_redis.set.assert_called_once()

    # Check that the key and value are correct
    args, kwargs = mock_redis.set.call_args
    assert args[0].startswith("test_prefix:test_timing:")
    assert "test_timing" in args[1]
    assert "ms" in args[1]
    assert kwargs["ex"] == 3600


@patch("app.core.monitoring.metrics.RedisCache")
def test_metrics_collector_record_count(mock_redis_cache):
    """Test that MetricsCollector.record_count works correctly."""
    # Create a mock Redis instance
    mock_redis = MagicMock()
    mock_redis_cache.return_value.redis = mock_redis

    # Create a collector
    collector = MetricsCollector(prefix="test_prefix", ttl=3600)

    # Record a count metric
    result = collector.record_count(
        name="test_count",
        value=42,
        tags={"tag1": "value1"},
    )

    # Check that the metric was recorded
    assert result is True
    mock_redis.set.assert_called_once()

    # Check that the key and value are correct
    args, kwargs = mock_redis.set.call_args
    assert args[0].startswith("test_prefix:test_count:")
    assert "test_count" in args[1]
    assert "42" in args[1]
    assert "count" in args[1]
    assert kwargs["ex"] == 3600


@patch("app.core.monitoring.metrics.RedisCache")
def test_metrics_collector_get_metrics(mock_redis_cache):
    """Test that MetricsCollector.get_metrics works correctly."""
    # Create a mock Redis instance
    mock_redis = MagicMock()
    mock_redis_cache.return_value.redis = mock_redis

    # Set up mock keys and values
    mock_redis.keys.return_value = [
        b"test_prefix:test_metric:1234567890",
        b"test_prefix:test_metric:1234567891",
    ]
    mock_redis.mget.return_value = [
        b'{"name":"test_metric","value":123.45,"unit":"ms","timestamp":"2023-01-01T00:00:00Z","tags":{"tag1":"value1"}}',
        b'{"name":"test_metric","value":456.78,"unit":"ms","timestamp":"2023-01-01T00:00:01Z","tags":{"tag1":"value2"}}',
    ]

    # Create a collector
    collector = MetricsCollector(prefix="test_prefix", ttl=3600)

    # Get metrics
    metrics = collector.get_metrics(name="test_metric", limit=10)

    # Check that the metrics were retrieved
    assert len(metrics) == 2
    assert metrics[0].name == "test_metric"
    assert metrics[0].value == 123.45
    assert metrics[0].unit == "ms"
    assert metrics[0].tags == {"tag1": "value1"}
    assert metrics[1].name == "test_metric"
    assert metrics[1].value == 456.78
    assert metrics[1].unit == "ms"
    assert metrics[1].tags == {"tag1": "value2"}


@patch("app.core.monitoring.metrics.metrics_collector")
def test_record_timing_function(mock_collector):
    """Test that record_timing function works correctly."""
    # Set up mock collector
    mock_collector.record_timing.return_value = True

    # Record a timing metric
    start_time = time.time() - 1  # 1 second ago
    result = record_timing(
        name="test_timing",
        start_time=start_time,
        tags={"tag1": "value1"},
    )

    # Check that the metric was recorded
    assert result is True
    mock_collector.record_timing.assert_called_once_with(
        "test_timing",
        start_time,
        {"tag1": "value1"},
    )


@patch("app.core.monitoring.metrics.metrics_collector")
def test_record_count_function(mock_collector):
    """Test that record_count function works correctly."""
    # Set up mock collector
    mock_collector.record_count.return_value = True

    # Record a count metric
    result = record_count(
        name="test_count",
        value=42,
        tags={"tag1": "value1"},
    )

    # Check that the metric was recorded
    assert result is True
    mock_collector.record_count.assert_called_once_with(
        "test_count",
        42,
        {"tag1": "value1"},
    )


@patch("app.core.monitoring.metrics.metrics_collector")
def test_get_metrics_function(mock_collector):
    """Test that get_metrics function works correctly."""
    # Set up mock collector
    mock_metrics = [
        PerformanceMetric(
            name="test_metric",
            value=123.45,
            unit="ms",
            timestamp=datetime(2023, 1, 1, tzinfo=timezone.utc),
            tags={"tag1": "value1"},
        ),
        PerformanceMetric(
            name="test_metric",
            value=456.78,
            unit="ms",
            timestamp=datetime(2023, 1, 2, tzinfo=timezone.utc),
            tags={"tag1": "value2"},
        ),
    ]
    mock_collector.get_metrics.return_value = mock_metrics

    # Get metrics
    start_time = datetime(2023, 1, 1, tzinfo=timezone.utc)
    end_time = datetime(2023, 1, 3, tzinfo=timezone.utc)
    metrics = get_metrics(
        name="test_metric",
        start_time=start_time,
        end_time=end_time,
        limit=10,
    )

    # Check that the metrics were retrieved
    assert metrics == mock_metrics
    mock_collector.get_metrics.assert_called_once_with(
        "test_metric",
        start_time,
        end_time,
        10,
    )
