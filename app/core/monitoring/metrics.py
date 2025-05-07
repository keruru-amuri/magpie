"""
Performance metrics collection for the MAGPIE platform.

This module provides functionality for collecting and storing performance metrics
for API calls, LLM interactions, and other operations.
"""

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union

from loguru import logger
from pydantic import BaseModel, Field

from app.core.cache.connection import RedisCache
from app.core.config import settings


class PerformanceMetric(BaseModel):
    """
    Model for performance metrics.
    
    Attributes:
        name: Name of the metric
        value: Value of the metric
        unit: Unit of measurement (ms, s, count, etc.)
        timestamp: Time when the metric was recorded
        tags: Additional tags for the metric
    """
    
    name: str
    value: Union[float, int]
    unit: str = "ms"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = Field(default_factory=dict)


class MetricsCollector:
    """
    Collector for performance metrics.
    
    This class provides methods for recording and retrieving performance metrics.
    It uses Redis for storing metrics temporarily for analysis.
    """
    
    def __init__(self, prefix: str = "metrics", ttl: int = 86400):
        """
        Initialize the metrics collector.
        
        Args:
            prefix: Prefix for Redis keys
            ttl: Time-to-live for metrics in seconds (default: 1 day)
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
                self.logger.warning(f"Failed to initialize Redis for metrics: {e}")
                self.enabled = False
        else:
            self.enabled = False
    
    def record_metric(self, metric: PerformanceMetric) -> bool:
        """
        Record a performance metric.
        
        Args:
            metric: Performance metric to record
            
        Returns:
            bool: True if the metric was recorded successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Create a key with timestamp for sorting
            timestamp = int(metric.timestamp.timestamp() * 1000)
            key = f"{self.prefix}:{metric.name}:{timestamp}"
            
            # Store the metric in Redis
            self.redis.redis.set(
                key,
                metric.model_dump_json(),
                ex=self.ttl
            )
            
            # Log the metric
            self.logger.debug(
                f"Recorded metric: {metric.name}={metric.value}{metric.unit}",
                metric=metric.model_dump()
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to record metric: {e}")
            return False
    
    def record_timing(
        self,
        name: str,
        start_time: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Record a timing metric.
        
        Args:
            name: Name of the metric
            start_time: Start time from time.time()
            tags: Additional tags for the metric
            
        Returns:
            bool: True if the metric was recorded successfully, False otherwise
        """
        # Calculate duration in milliseconds
        duration_ms = (time.time() - start_time) * 1000
        
        # Create metric
        metric = PerformanceMetric(
            name=name,
            value=duration_ms,
            unit="ms",
            tags=tags or {}
        )
        
        # Record metric
        return self.record_metric(metric)
    
    def record_count(
        self,
        name: str,
        value: int = 1,
        tags: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Record a count metric.
        
        Args:
            name: Name of the metric
            value: Count value
            tags: Additional tags for the metric
            
        Returns:
            bool: True if the metric was recorded successfully, False otherwise
        """
        # Create metric
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit="count",
            tags=tags or {}
        )
        
        # Record metric
        return self.record_metric(metric)
    
    def get_metrics(
        self,
        name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[PerformanceMetric]:
        """
        Get metrics from Redis.
        
        Args:
            name: Filter by metric name
            start_time: Start time for filtering
            end_time: End time for filtering
            limit: Maximum number of metrics to return
            
        Returns:
            List[PerformanceMetric]: List of performance metrics
        """
        if not self.enabled:
            return []
        
        try:
            # Create pattern for keys
            pattern = f"{self.prefix}:{name or '*'}:*"
            
            # Get keys matching the pattern
            keys = self.redis.redis.keys(pattern)
            
            # Sort keys by timestamp (embedded in the key)
            keys = sorted(keys, reverse=True)[:limit]
            
            # Get values for keys
            if not keys:
                return []
            
            values = self.redis.redis.mget(keys)
            
            # Parse values into metrics
            metrics = []
            for value in values:
                if value:
                    try:
                        metric_dict = value.decode("utf-8")
                        metric = PerformanceMetric.model_validate_json(metric_dict)
                        
                        # Filter by time range if provided
                        if start_time and metric.timestamp < start_time:
                            continue
                        if end_time and metric.timestamp > end_time:
                            continue
                        
                        metrics.append(metric)
                    except Exception as e:
                        self.logger.error(f"Failed to parse metric: {e}")
            
            return metrics
        except Exception as e:
            self.logger.error(f"Failed to get metrics: {e}")
            return []


# Create a global metrics collector instance
metrics_collector = MetricsCollector()


def record_timing(
    name: str,
    start_time: float,
    tags: Optional[Dict[str, str]] = None,
) -> bool:
    """
    Record a timing metric.
    
    Args:
        name: Name of the metric
        start_time: Start time from time.time()
        tags: Additional tags for the metric
        
    Returns:
        bool: True if the metric was recorded successfully, False otherwise
    """
    return metrics_collector.record_timing(name, start_time, tags)


def record_count(
    name: str,
    value: int = 1,
    tags: Optional[Dict[str, str]] = None,
) -> bool:
    """
    Record a count metric.
    
    Args:
        name: Name of the metric
        value: Count value
        tags: Additional tags for the metric
        
    Returns:
        bool: True if the metric was recorded successfully, False otherwise
    """
    return metrics_collector.record_count(name, value, tags)


def get_metrics(
    name: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
) -> List[PerformanceMetric]:
    """
    Get metrics from Redis.
    
    Args:
        name: Filter by metric name
        start_time: Start time for filtering
        end_time: End time for filtering
        limit: Maximum number of metrics to return
        
    Returns:
        List[PerformanceMetric]: List of performance metrics
    """
    return metrics_collector.get_metrics(name, start_time, end_time, limit)
