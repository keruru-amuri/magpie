"""
Unit tests for analytics module.
"""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.core.monitoring.analytics import (
    ModelSize,
    ModelPricing,
    UsageRecord,
    AnalyticsPeriod,
    UsageAnalytics,
    record_usage,
    get_user_metrics,
    get_model_metrics,
    get_agent_metrics,
    get_global_metrics,
    get_usage_records,
)


def test_model_pricing():
    """Test that ModelPricing works correctly."""
    # Create a pricing model
    pricing = ModelPricing(
        model_size=ModelSize.MEDIUM,
        input_cost_per_1m_tokens=0.40,
        output_cost_per_1m_tokens=1.60,
    )

    # Calculate cost
    cost = pricing.calculate_cost(input_tokens=1000, output_tokens=500)

    # Check that the cost is calculated correctly
    expected_cost = (1000 / 1_000_000) * 0.40 + (500 / 1_000_000) * 1.60
    assert cost == expected_cost


def test_usage_record():
    """Test that UsageRecord works correctly."""
    # Create a usage record
    record = UsageRecord(
        model_size=ModelSize.LARGE,
        agent_type="test_agent",
        user_id="test_user",
        conversation_id="test_conversation",
        request_id="test_request",
        input_tokens=1000,
        output_tokens=500,
        latency_ms=150.5,
    )

    # Check that the record has the expected values
    assert record.model_size == ModelSize.LARGE
    assert record.agent_type == "test_agent"
    assert record.user_id == "test_user"
    assert record.conversation_id == "test_conversation"
    assert record.request_id == "test_request"
    assert record.input_tokens == 1000
    assert record.output_tokens == 500
    assert record.total_tokens == 1500
    assert record.latency_ms == 150.5

    # Check that the cost is calculated correctly
    expected_cost = (1000 / 1_000_000) * 2.00 + (500 / 1_000_000) * 8.00
    assert record.cost == expected_cost


@patch("app.core.monitoring.analytics.RedisCache")
def test_usage_analytics_init(mock_redis_cache):
    """Test that UsageAnalytics initializes correctly."""
    # Create an analytics service
    analytics = UsageAnalytics(prefix="test_prefix", ttl=3600)

    # Check that the service has the expected values
    assert analytics.prefix == "test_prefix"
    assert analytics.ttl == 3600
    assert analytics.enabled is True

    # Check that Redis was initialized
    mock_redis_cache.assert_called_once_with(prefix="test_prefix")


@patch("app.core.monitoring.analytics.RedisCache")
def test_record_usage(mock_redis_cache):
    """Test that record_usage works correctly."""
    # Create a mock Redis instance
    mock_redis = MagicMock()
    mock_redis_cache.return_value.redis = mock_redis

    # Create an analytics service
    analytics = UsageAnalytics(prefix="test_prefix", ttl=3600)

    # Create a usage record
    record = UsageRecord(
        model_size=ModelSize.MEDIUM,
        agent_type="test_agent",
        user_id="test_user",
        conversation_id="test_conversation",
        request_id="test_request",
        input_tokens=1000,
        output_tokens=500,
    )

    # Record usage
    result = analytics.record_usage(record)

    # Check that the usage was recorded
    assert result is True

    # Check that the record was stored in Redis
    mock_redis.set.assert_called_once()
    args, kwargs = mock_redis.set.call_args
    assert args[0].startswith("usage:")
    assert kwargs["ex"] == 3600

    # Check that metrics were updated
    assert mock_redis.hmset.call_count >= 4  # User, model, agent, and global metrics


@patch("app.core.monitoring.analytics.analytics_service")
def test_record_usage_function(mock_analytics_service):
    """Test that record_usage function works correctly."""
    # Set up mock analytics service
    mock_analytics_service.record_usage.return_value = True

    # Record usage
    result = record_usage(
        model_size=ModelSize.MEDIUM,
        agent_type="test_agent",
        input_tokens=1000,
        output_tokens=500,
        user_id="test_user",
        conversation_id="test_conversation",
        request_id="test_request",
        latency_ms=150.5,
    )

    # Check that the usage was recorded
    assert result is not None

    # Check that the analytics service was called
    mock_analytics_service.record_usage.assert_called_once()
    args, kwargs = mock_analytics_service.record_usage.call_args
    usage_record = args[0]
    assert usage_record.model_size == ModelSize.MEDIUM
    assert usage_record.agent_type == "test_agent"
    assert usage_record.input_tokens == 1000
    assert usage_record.output_tokens == 500
    assert usage_record.user_id == "test_user"
    assert usage_record.conversation_id == "test_conversation"
    assert usage_record.request_id == "test_request"
    assert usage_record.latency_ms == 150.5


@patch("app.core.monitoring.analytics.analytics_service")
def test_get_user_metrics_function(mock_analytics_service):
    """Test that get_user_metrics function works correctly."""
    # Set up mock analytics service
    mock_analytics_service.get_user_metrics.return_value = {"test": "data"}

    # Get user metrics
    result = get_user_metrics(
        user_id="test_user",
        period=AnalyticsPeriod.DAILY,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc),
    )

    # Check that the metrics were retrieved
    assert result == {"test": "data"}

    # Check that the analytics service was called
    assert mock_analytics_service.get_user_metrics.call_count == 1
    args, kwargs = mock_analytics_service.get_user_metrics.call_args
    assert args[0] == "test_user"
    assert args[1] == AnalyticsPeriod.DAILY


@patch("app.core.monitoring.analytics.analytics_service")
def test_get_model_metrics_function(mock_analytics_service):
    """Test that get_model_metrics function works correctly."""
    # Set up mock analytics service
    mock_analytics_service.get_model_metrics.return_value = {"test": "data"}

    # Get model metrics
    result = get_model_metrics(
        model_size=ModelSize.MEDIUM,
        period=AnalyticsPeriod.DAILY,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc),
    )

    # Check that the metrics were retrieved
    assert result == {"test": "data"}

    # Check that the analytics service was called
    assert mock_analytics_service.get_model_metrics.call_count == 1
    args = mock_analytics_service.get_model_metrics.call_args[0]
    assert args[0] == ModelSize.MEDIUM
    assert args[1] == AnalyticsPeriod.DAILY


@patch("app.core.monitoring.analytics.analytics_service")
def test_get_agent_metrics_function(mock_analytics_service):
    """Test that get_agent_metrics function works correctly."""
    # Set up mock analytics service
    mock_analytics_service.get_agent_metrics.return_value = {"test": "data"}

    # Get agent metrics
    result = get_agent_metrics(
        agent_type="test_agent",
        period=AnalyticsPeriod.DAILY,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc),
    )

    # Check that the metrics were retrieved
    assert result == {"test": "data"}

    # Check that the analytics service was called
    assert mock_analytics_service.get_agent_metrics.call_count == 1
    args = mock_analytics_service.get_agent_metrics.call_args[0]
    assert args[0] == "test_agent"
    assert args[1] == AnalyticsPeriod.DAILY


@patch("app.core.monitoring.analytics.analytics_service")
def test_get_global_metrics_function(mock_analytics_service):
    """Test that get_global_metrics function works correctly."""
    # Set up mock analytics service
    mock_analytics_service.get_global_metrics.return_value = {"test": "data"}

    # Get global metrics
    result = get_global_metrics(
        period=AnalyticsPeriod.DAILY,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc),
    )

    # Check that the metrics were retrieved
    assert result == {"test": "data"}

    # Check that the analytics service was called
    assert mock_analytics_service.get_global_metrics.call_count == 1
    args = mock_analytics_service.get_global_metrics.call_args[0]
    assert args[0] == AnalyticsPeriod.DAILY


@patch("app.core.monitoring.analytics.analytics_service")
def test_get_usage_records_function(mock_analytics_service):
    """Test that get_usage_records function works correctly."""
    # Set up mock analytics service
    mock_analytics_service.get_usage_records.return_value = [{"test": "data"}]

    # Get usage records
    result = get_usage_records(
        user_id="test_user",
        model_size=ModelSize.MEDIUM,
        agent_type="test_agent",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc),
        limit=10,
    )

    # Check that the records were retrieved
    assert result == [{"test": "data"}]

    # Check that the analytics service was called
    assert mock_analytics_service.get_usage_records.call_count == 1
    args = mock_analytics_service.get_usage_records.call_args[0]
    assert args[0] == "test_user"
    assert args[1] == ModelSize.MEDIUM
    assert args[2] == "test_agent"
