"""
Usage analytics and cost tracking for the MAGPIE platform.

This module provides functionality for tracking API usage, token consumption,
and cost metrics for LLM interactions.
"""

import json
import time
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple

from loguru import logger
from pydantic import BaseModel, Field

from app.core.cache.connection import RedisCache
from app.core.config import settings


class ModelSize(str, Enum):
    """
    Enum for model sizes.

    Attributes:
        SMALL: Small model (GPT-4.1-nano)
        MEDIUM: Medium model (GPT-4.1-mini)
        LARGE: Large model (GPT-4.1)
    """

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class ModelPricing(BaseModel):
    """
    Model for LLM pricing information.

    Attributes:
        model_size: Size of the model
        input_cost_per_1m_tokens: Cost per 1M input tokens
        output_cost_per_1m_tokens: Cost per 1M output tokens
    """

    model_size: ModelSize
    input_cost_per_1m_tokens: float
    output_cost_per_1m_tokens: float

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate the cost for a given number of tokens.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            float: Cost in USD
        """
        input_cost = (input_tokens / 1_000_000) * self.input_cost_per_1m_tokens
        output_cost = (output_tokens / 1_000_000) * self.output_cost_per_1m_tokens
        return input_cost + output_cost


class UsageRecord(BaseModel):
    """
    Model for API usage records.

    Attributes:
        id: Unique identifier for the usage record
        timestamp: Time when the usage was recorded
        model_size: Size of the model used
        agent_type: Type of agent that used the model
        user_id: ID of the user who made the request
        conversation_id: ID of the conversation
        request_id: ID of the request
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        total_tokens: Total number of tokens
        cost: Cost of the request in USD
        latency_ms: Latency of the request in milliseconds
    """

    id: str = Field(default_factory=lambda: f"usage_{datetime.now(timezone.utc).timestamp()}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_size: ModelSize
    agent_type: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    request_id: Optional[str] = None
    input_tokens: int
    output_tokens: int
    total_tokens: int = 0
    cost: float = 0.0
    latency_ms: Optional[float] = None

    def __init__(self, **data):
        """
        Initialize the usage record.

        Args:
            **data: Data for the usage record
        """
        super().__init__(**data)

        # Calculate total tokens if not provided
        if not self.total_tokens:
            self.total_tokens = self.input_tokens + self.output_tokens

        # Calculate cost if not provided
        if not self.cost:
            pricing = MODEL_PRICING_MAP.get(self.model_size)
            if pricing:
                self.cost = pricing.calculate_cost(self.input_tokens, self.output_tokens)


# Define model pricing based on OpenAI's GPT-4.1 pricing
MODEL_PRICING_MAP = {
    ModelSize.SMALL: ModelPricing(
        model_size=ModelSize.SMALL,
        input_cost_per_1m_tokens=0.10,
        output_cost_per_1m_tokens=0.40,
    ),
    ModelSize.MEDIUM: ModelPricing(
        model_size=ModelSize.MEDIUM,
        input_cost_per_1m_tokens=0.40,
        output_cost_per_1m_tokens=1.60,
    ),
    ModelSize.LARGE: ModelPricing(
        model_size=ModelSize.LARGE,
        input_cost_per_1m_tokens=2.00,
        output_cost_per_1m_tokens=8.00,
    ),
}


class AnalyticsPeriod(str, Enum):
    """
    Enum for analytics time periods.

    Attributes:
        DAILY: Daily analytics
        WEEKLY: Weekly analytics
        MONTHLY: Monthly analytics
        ALL_TIME: All-time analytics
    """

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"


class UsageAnalytics:
    """
    Service for tracking and analyzing API usage.

    This class provides methods for recording and retrieving usage analytics.
    It uses Redis for storing analytics data.
    """

    def __init__(self, prefix: str = "analytics", ttl: int = 2592000):  # 30 days
        """
        Initialize the usage analytics service.

        Args:
            prefix: Prefix for Redis keys
            ttl: Time-to-live for analytics data in seconds (default: 30 days)
        """
        self.prefix = prefix
        self.ttl = ttl
        self.logger = logger.bind(name=__name__)

        # Initialize Redis cache if not in testing mode
        if settings.ENVIRONMENT != "testing":
            try:
                self.redis = RedisCache(prefix=prefix)
                self.enabled = True
            except Exception as e:
                self.logger.warning(f"Failed to initialize Redis for analytics: {e}")
                self.enabled = False
        else:
            self.enabled = False

    def record_usage(self, usage: UsageRecord) -> bool:
        """
        Record API usage.

        Args:
            usage: Usage record to store

        Returns:
            bool: True if the usage was recorded successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Store the usage record
            usage_key = f"usage:{usage.id}"
            self.redis.redis.set(
                usage_key,
                usage.model_dump_json(),
                ex=self.ttl
            )

            # Update aggregated metrics
            self._update_user_metrics(usage)
            self._update_model_metrics(usage)
            self._update_agent_metrics(usage)
            self._update_global_metrics(usage)

            # Log the usage
            self.logger.debug(
                f"Recorded usage: {usage.model_size} model, {usage.total_tokens} tokens, ${usage.cost:.4f}",
                usage=usage.model_dump()
            )

            return True
        except Exception as e:
            self.logger.error(f"Failed to record usage: {e}")
            return False

    def _update_user_metrics(self, usage: UsageRecord) -> None:
        """
        Update user-specific metrics.

        Args:
            usage: Usage record
        """
        if not usage.user_id:
            return

        # Get current date for time-based keys
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        month_str = now.strftime("%Y-%m")

        # Update daily user metrics
        daily_key = f"user:{usage.user_id}:daily:{date_str}"
        self._increment_metrics(daily_key, usage)

        # Update monthly user metrics
        monthly_key = f"user:{usage.user_id}:monthly:{month_str}"
        self._increment_metrics(monthly_key, usage)

        # Update all-time user metrics
        all_time_key = f"user:{usage.user_id}:all_time"
        self._increment_metrics(all_time_key, usage)

    def _update_model_metrics(self, usage: UsageRecord) -> None:
        """
        Update model-specific metrics.

        Args:
            usage: Usage record
        """
        # Get current date for time-based keys
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        month_str = now.strftime("%Y-%m")

        # Update daily model metrics
        daily_key = f"model:{usage.model_size}:daily:{date_str}"
        self._increment_metrics(daily_key, usage)

        # Update monthly model metrics
        monthly_key = f"model:{usage.model_size}:monthly:{month_str}"
        self._increment_metrics(monthly_key, usage)

        # Update all-time model metrics
        all_time_key = f"model:{usage.model_size}:all_time"
        self._increment_metrics(all_time_key, usage)

    def _update_agent_metrics(self, usage: UsageRecord) -> None:
        """
        Update agent-specific metrics.

        Args:
            usage: Usage record
        """
        # Get current date for time-based keys
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        month_str = now.strftime("%Y-%m")

        # Update daily agent metrics
        daily_key = f"agent:{usage.agent_type}:daily:{date_str}"
        self._increment_metrics(daily_key, usage)

        # Update monthly agent metrics
        monthly_key = f"agent:{usage.agent_type}:monthly:{month_str}"
        self._increment_metrics(monthly_key, usage)

        # Update all-time agent metrics
        all_time_key = f"agent:{usage.agent_type}:all_time"
        self._increment_metrics(all_time_key, usage)

    def _update_global_metrics(self, usage: UsageRecord) -> None:
        """
        Update global metrics.

        Args:
            usage: Usage record
        """
        # Get current date for time-based keys
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        month_str = now.strftime("%Y-%m")

        # Update daily global metrics
        daily_key = f"global:daily:{date_str}"
        self._increment_metrics(daily_key, usage)

        # Update monthly global metrics
        monthly_key = f"global:monthly:{month_str}"
        self._increment_metrics(monthly_key, usage)

        # Update all-time global metrics
        all_time_key = f"global:all_time"
        self._increment_metrics(all_time_key, usage)

    def _increment_metrics(self, key: str, usage: UsageRecord) -> None:
        """
        Increment metrics for a specific key.

        Args:
            key: Redis key
            usage: Usage record
        """
        # Get current metrics
        metrics = self.redis.redis.hgetall(key)

        # Convert bytes to strings
        metrics = {k.decode("utf-8"): float(v.decode("utf-8")) for k, v in metrics.items()} if metrics else {}

        # Update metrics
        metrics["request_count"] = metrics.get("request_count", 0) + 1
        metrics["input_tokens"] = metrics.get("input_tokens", 0) + usage.input_tokens
        metrics["output_tokens"] = metrics.get("output_tokens", 0) + usage.output_tokens
        metrics["total_tokens"] = metrics.get("total_tokens", 0) + usage.total_tokens
        metrics["cost"] = metrics.get("cost", 0) + usage.cost

        # Store updated metrics
        self.redis.redis.hmset(key, metrics)
        self.redis.redis.expire(key, self.ttl)

    def get_user_metrics(
        self,
        user_id: str,
        period: AnalyticsPeriod = AnalyticsPeriod.DAILY,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get metrics for a specific user.

        Args:
            user_id: User ID
            period: Analytics period
            start_date: Start date for filtering
            end_date: End date for filtering

        Returns:
            Dict[str, Any]: User metrics
        """
        if not self.enabled:
            return {}

        try:
            if period == AnalyticsPeriod.ALL_TIME:
                # Get all-time metrics
                key = f"user:{user_id}:all_time"
                metrics = self._get_metrics(key)
                return {
                    "user_id": user_id,
                    "period": period,
                    "metrics": metrics,
                }
            else:
                # Get time-based metrics
                metrics_by_date = self._get_time_based_metrics(
                    prefix=f"user:{user_id}",
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                )

                return {
                    "user_id": user_id,
                    "period": period,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "metrics_by_date": metrics_by_date,
                    "total": self._aggregate_metrics(metrics_by_date.values()),
                }
        except Exception as e:
            self.logger.error(f"Failed to get user metrics: {e}")
            return {}

    def get_model_metrics(
        self,
        model_size: ModelSize,
        period: AnalyticsPeriod = AnalyticsPeriod.DAILY,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get metrics for a specific model.

        Args:
            model_size: Model size
            period: Analytics period
            start_date: Start date for filtering
            end_date: End date for filtering

        Returns:
            Dict[str, Any]: Model metrics
        """
        if not self.enabled:
            return {}

        try:
            if period == AnalyticsPeriod.ALL_TIME:
                # Get all-time metrics
                key = f"model:{model_size}:all_time"
                metrics = self._get_metrics(key)
                return {
                    "model_size": model_size,
                    "period": period,
                    "metrics": metrics,
                }
            else:
                # Get time-based metrics
                metrics_by_date = self._get_time_based_metrics(
                    prefix=f"model:{model_size}",
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                )

                return {
                    "model_size": model_size,
                    "period": period,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "metrics_by_date": metrics_by_date,
                    "total": self._aggregate_metrics(metrics_by_date.values()),
                }
        except Exception as e:
            self.logger.error(f"Failed to get model metrics: {e}")
            return {}

    def get_agent_metrics(
        self,
        agent_type: str,
        period: AnalyticsPeriod = AnalyticsPeriod.DAILY,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get metrics for a specific agent.

        Args:
            agent_type: Agent type
            period: Analytics period
            start_date: Start date for filtering
            end_date: End date for filtering

        Returns:
            Dict[str, Any]: Agent metrics
        """
        if not self.enabled:
            return {}

        try:
            if period == AnalyticsPeriod.ALL_TIME:
                # Get all-time metrics
                key = f"agent:{agent_type}:all_time"
                metrics = self._get_metrics(key)
                return {
                    "agent_type": agent_type,
                    "period": period,
                    "metrics": metrics,
                }
            else:
                # Get time-based metrics
                metrics_by_date = self._get_time_based_metrics(
                    prefix=f"agent:{agent_type}",
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                )

                return {
                    "agent_type": agent_type,
                    "period": period,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "metrics_by_date": metrics_by_date,
                    "total": self._aggregate_metrics(metrics_by_date.values()),
                }
        except Exception as e:
            self.logger.error(f"Failed to get agent metrics: {e}")
            return {}

    def get_global_metrics(
        self,
        period: AnalyticsPeriod = AnalyticsPeriod.DAILY,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get global metrics.

        Args:
            period: Analytics period
            start_date: Start date for filtering
            end_date: End date for filtering

        Returns:
            Dict[str, Any]: Global metrics
        """
        if not self.enabled:
            return {}

        try:
            if period == AnalyticsPeriod.ALL_TIME:
                # Get all-time metrics
                key = "global:all_time"
                metrics = self._get_metrics(key)
                return {
                    "period": period,
                    "metrics": metrics,
                }
            else:
                # Get time-based metrics
                metrics_by_date = self._get_time_based_metrics(
                    prefix="global",
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                )

                return {
                    "period": period,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "metrics_by_date": metrics_by_date,
                    "total": self._aggregate_metrics(metrics_by_date.values()),
                }
        except Exception as e:
            self.logger.error(f"Failed to get global metrics: {e}")
            return {}

    def get_usage_records(
        self,
        user_id: Optional[str] = None,
        model_size: Optional[ModelSize] = None,
        agent_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[UsageRecord]:
        """
        Get usage records.

        Args:
            user_id: Filter by user ID
            model_size: Filter by model size
            agent_type: Filter by agent type
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of records to return

        Returns:
            List[UsageRecord]: List of usage records
        """
        if not self.enabled:
            return []

        try:
            # Get all usage records
            pattern = f"{self.prefix}:usage:*"
            keys = self.redis.redis.keys(pattern)

            # Sort keys by timestamp (newest first)
            keys = sorted(keys, reverse=True)[:limit * 2]  # Get more than needed for filtering

            # Get values for keys
            if not keys:
                return []

            values = self.redis.redis.mget(keys)

            # Parse values into usage records
            records = []
            for value in values:
                if value:
                    try:
                        record_dict = json.loads(value.decode("utf-8"))
                        record = UsageRecord.model_validate(record_dict)

                        # Apply filters
                        if user_id and record.user_id != user_id:
                            continue
                        if model_size and record.model_size != model_size:
                            continue
                        if agent_type and record.agent_type != agent_type:
                            continue
                        if start_date and record.timestamp < start_date:
                            continue
                        if end_date and record.timestamp > end_date:
                            continue

                        records.append(record)

                        # Check limit after filtering
                        if len(records) >= limit:
                            break
                    except Exception as e:
                        self.logger.error(f"Failed to parse usage record: {e}")

            return records
        except Exception as e:
            self.logger.error(f"Failed to get usage records: {e}")
            return []

    def _get_metrics(self, key: str) -> Dict[str, float]:
        """
        Get metrics for a specific key.

        Args:
            key: Redis key

        Returns:
            Dict[str, float]: Metrics
        """
        # Get metrics
        metrics = self.redis.redis.hgetall(key)

        # Convert bytes to strings and floats
        return {k.decode("utf-8"): float(v.decode("utf-8")) for k, v in metrics.items()} if metrics else {}

    def _get_time_based_metrics(
        self,
        prefix: str,
        period: AnalyticsPeriod,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Get time-based metrics.

        Args:
            prefix: Prefix for Redis keys
            period: Analytics period
            start_date: Start date for filtering
            end_date: End date for filtering

        Returns:
            Dict[str, Dict[str, float]]: Metrics by date
        """
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.now(timezone.utc)

        if not start_date:
            if period == AnalyticsPeriod.DAILY:
                # Default to last 7 days
                start_date = end_date - timedelta(days=6)
            elif period == AnalyticsPeriod.WEEKLY:
                # Default to last 4 weeks
                start_date = end_date - timedelta(weeks=3)
            elif period == AnalyticsPeriod.MONTHLY:
                # Default to last 6 months
                start_date = end_date - timedelta(days=5 * 30)

        # Generate date range
        date_range = []
        if period == AnalyticsPeriod.DAILY:
            # Generate daily dates
            current_date = start_date
            while current_date <= end_date:
                date_range.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(days=1)
        elif period == AnalyticsPeriod.WEEKLY:
            # Generate weekly dates (starting from Monday)
            current_date = start_date - timedelta(days=start_date.weekday())
            while current_date <= end_date:
                date_range.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(weeks=1)
        elif period == AnalyticsPeriod.MONTHLY:
            # Generate monthly dates
            current_date = datetime(start_date.year, start_date.month, 1, tzinfo=timezone.utc)
            while current_date <= end_date:
                date_range.append(current_date.strftime("%Y-%m"))
                # Move to next month
                if current_date.month == 12:
                    current_date = datetime(current_date.year + 1, 1, 1, tzinfo=timezone.utc)
                else:
                    current_date = datetime(current_date.year, current_date.month + 1, 1, tzinfo=timezone.utc)

        # Get metrics for each date
        metrics_by_date = {}
        for date_str in date_range:
            if period == AnalyticsPeriod.MONTHLY:
                key = f"{prefix}:monthly:{date_str}"
            else:
                key = f"{prefix}:daily:{date_str}"

            metrics = self._get_metrics(key)

            if metrics:
                metrics_by_date[date_str] = metrics

        return metrics_by_date

    def _aggregate_metrics(self, metrics_list: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Aggregate metrics from multiple sources.

        Args:
            metrics_list: List of metrics dictionaries

        Returns:
            Dict[str, float]: Aggregated metrics
        """
        if not metrics_list:
            return {}

        # Initialize aggregated metrics
        aggregated = {
            "request_count": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cost": 0,
        }

        # Aggregate metrics
        for metrics in metrics_list:
            for key in aggregated:
                aggregated[key] += metrics.get(key, 0)

        return aggregated


# Create a global analytics instance
analytics_service = UsageAnalytics()


def record_usage(
    model_size: ModelSize,
    agent_type: str,
    input_tokens: int,
    output_tokens: int,
    user_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    request_id: Optional[str] = None,
    latency_ms: Optional[float] = None,
) -> Optional[UsageRecord]:
    """
    Record API usage.

    Args:
        model_size: Size of the model used
        agent_type: Type of agent that used the model
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        user_id: ID of the user who made the request
        conversation_id: ID of the conversation
        request_id: ID of the request
        latency_ms: Latency of the request in milliseconds

    Returns:
        Optional[UsageRecord]: Usage record if recorded successfully, None otherwise
    """
    # Create usage record
    usage = UsageRecord(
        model_size=model_size,
        agent_type=agent_type,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        user_id=user_id,
        conversation_id=conversation_id,
        request_id=request_id,
        latency_ms=latency_ms,
    )

    # Record usage
    success = analytics_service.record_usage(usage)

    return usage if success else None


def get_user_metrics(
    user_id: str,
    period: AnalyticsPeriod = AnalyticsPeriod.DAILY,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Get metrics for a specific user.

    Args:
        user_id: User ID
        period: Analytics period
        start_date: Start date for filtering
        end_date: End date for filtering

    Returns:
        Dict[str, Any]: User metrics
    """
    return analytics_service.get_user_metrics(user_id, period, start_date, end_date)


def get_model_metrics(
    model_size: ModelSize,
    period: AnalyticsPeriod = AnalyticsPeriod.DAILY,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Get metrics for a specific model.

    Args:
        model_size: Model size
        period: Analytics period
        start_date: Start date for filtering
        end_date: End date for filtering

    Returns:
        Dict[str, Any]: Model metrics
    """
    return analytics_service.get_model_metrics(model_size, period, start_date, end_date)


def get_agent_metrics(
    agent_type: str,
    period: AnalyticsPeriod = AnalyticsPeriod.DAILY,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Get metrics for a specific agent.

    Args:
        agent_type: Agent type
        period: Analytics period
        start_date: Start date for filtering
        end_date: End date for filtering

    Returns:
        Dict[str, Any]: Agent metrics
    """
    return analytics_service.get_agent_metrics(agent_type, period, start_date, end_date)


def get_global_metrics(
    period: AnalyticsPeriod = AnalyticsPeriod.DAILY,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Get global metrics.

    Args:
        period: Analytics period
        start_date: Start date for filtering
        end_date: End date for filtering

    Returns:
        Dict[str, Any]: Global metrics
    """
    return analytics_service.get_global_metrics(period, start_date, end_date)


def get_usage_records(
    user_id: Optional[str] = None,
    model_size: Optional[ModelSize] = None,
    agent_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
) -> List[UsageRecord]:
    """
    Get usage records.

    Args:
        user_id: Filter by user ID
        model_size: Filter by model size
        agent_type: Filter by agent type
        start_date: Start date for filtering
        end_date: End date for filtering
        limit: Maximum number of records to return

    Returns:
        List[UsageRecord]: List of usage records
    """
    return analytics_service.get_usage_records(
        user_id, model_size, agent_type, start_date, end_date, limit
    )
