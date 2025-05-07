"""
Performance test harness for measuring response times and resource usage.

This module provides utilities for measuring response times, throughput, and resource usage.
"""
import time
import logging
import asyncio
import statistics
import psutil
import platform
import os
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Enum for metric types."""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    TOKEN_COUNT = "token_count"
    TOKEN_RATE = "token_rate"


class PerformanceMetric:
    """
    Model for performance metrics.
    """
    
    def __init__(
        self,
        name: str,
        value: float,
        unit: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a performance metric.
        
        Args:
            name: Metric name
            value: Metric value
            unit: Metric unit
            timestamp: Optional timestamp
            metadata: Optional metadata
        """
        self.name = name
        self.value = value
        self.unit = unit
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class PerformanceHarness:
    """
    Harness for measuring performance metrics.
    """
    
    def __init__(self):
        """Initialize the performance harness."""
        self.metrics = []
        self.start_time = datetime.now()
        self.end_time = None
    
    def record_metric(self, metric: PerformanceMetric):
        """
        Record a performance metric.
        
        Args:
            metric: Performance metric
        """
        self.metrics.append(metric)
    
    def get_metrics(
        self,
        name: Optional[str] = None,
        unit: Optional[str] = None
    ) -> List[PerformanceMetric]:
        """
        Get metrics matching the specified criteria.
        
        Args:
            name: Optional metric name
            unit: Optional metric unit
            
        Returns:
            List of matching metrics
        """
        result = []
        
        for metric in self.metrics:
            if name and metric.name != name:
                continue
            
            if unit and metric.unit != unit:
                continue
            
            result.append(metric)
        
        return result
    
    def get_metric_average(
        self,
        name: str,
        unit: Optional[str] = None
    ) -> Optional[float]:
        """
        Get average value of metrics matching the specified criteria.
        
        Args:
            name: Metric name
            unit: Optional metric unit
            
        Returns:
            Average metric value or None if no matching metrics
        """
        metrics = self.get_metrics(name=name, unit=unit)
        
        if not metrics:
            return None
        
        return statistics.mean(metric.value for metric in metrics)
    
    def get_metric_statistics(
        self,
        name: str,
        unit: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Get statistics for metrics matching the specified criteria.
        
        Args:
            name: Metric name
            unit: Optional metric unit
            
        Returns:
            Dictionary of statistics
        """
        metrics = self.get_metrics(name=name, unit=unit)
        
        if not metrics:
            return {
                "count": 0,
                "min": None,
                "max": None,
                "mean": None,
                "median": None,
                "stdev": None,
                "p90": None,
                "p95": None,
                "p99": None
            }
        
        values = [metric.value for metric in metrics]
        
        result = {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values)
        }
        
        if len(values) > 1:
            result["stdev"] = statistics.stdev(values)
        else:
            result["stdev"] = 0
        
        # Calculate percentiles
        sorted_values = sorted(values)
        result["p90"] = sorted_values[int(0.9 * len(sorted_values))]
        result["p95"] = sorted_values[int(0.95 * len(sorted_values))]
        result["p99"] = sorted_values[int(0.99 * len(sorted_values))]
        
        return result
    
    def clear(self):
        """Clear all recorded metrics."""
        self.metrics = []
        self.start_time = datetime.now()
        self.end_time = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        self.end_time = self.end_time or datetime.now()
        
        return {
            "metrics": [metric.to_dict() for metric in self.metrics],
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration": (self.end_time - self.start_time).total_seconds(),
            "metric_count": len(self.metrics)
        }


class TimingContext:
    """
    Context manager for timing code execution.
    """
    
    def __init__(
        self,
        harness: PerformanceHarness,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize timing context.
        
        Args:
            harness: Performance harness
            name: Metric name
            metadata: Optional metadata
        """
        self.harness = harness
        self.name = name
        self.metadata = metadata or {}
        self.start_time = None
    
    def __enter__(self):
        """Enter context manager."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        end_time = time.time()
        duration = end_time - self.start_time
        
        # Record metric
        self.harness.record_metric(PerformanceMetric(
            name=self.name,
            value=duration,
            unit="seconds",
            metadata=self.metadata
        ))


class AsyncTimingContext:
    """
    Async context manager for timing code execution.
    """
    
    def __init__(
        self,
        harness: PerformanceHarness,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize async timing context.
        
        Args:
            harness: Performance harness
            name: Metric name
            metadata: Optional metadata
        """
        self.harness = harness
        self.name = name
        self.metadata = metadata or {}
        self.start_time = None
    
    async def __aenter__(self):
        """Enter async context manager."""
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        end_time = time.time()
        duration = end_time - self.start_time
        
        # Record metric
        self.harness.record_metric(PerformanceMetric(
            name=self.name,
            value=duration,
            unit="seconds",
            metadata=self.metadata
        ))


class ResourceMonitor:
    """
    Monitor for system resource usage.
    """
    
    def __init__(
        self,
        harness: PerformanceHarness,
        interval: float = 1.0,
        monitor_cpu: bool = True,
        monitor_memory: bool = True
    ):
        """
        Initialize resource monitor.
        
        Args:
            harness: Performance harness
            interval: Monitoring interval in seconds
            monitor_cpu: Whether to monitor CPU usage
            monitor_memory: Whether to monitor memory usage
        """
        self.harness = harness
        self.interval = interval
        self.monitor_cpu = monitor_cpu
        self.monitor_memory = monitor_memory
        self.running = False
        self.thread = None
    
    def start(self):
        """Start monitoring."""
        if self.running:
            return
        
        self.running = True
        
        # Start monitoring in a separate thread
        self.thread = ThreadPoolExecutor(max_workers=1).submit(self._monitor)
    
    def stop(self):
        """Stop monitoring."""
        self.running = False
        
        if self.thread:
            self.thread.result()
            self.thread = None
    
    def _monitor(self):
        """Monitor system resources."""
        process = psutil.Process(os.getpid())
        
        while self.running:
            # Monitor CPU usage
            if self.monitor_cpu:
                cpu_percent = process.cpu_percent(interval=0.1)
                
                self.harness.record_metric(PerformanceMetric(
                    name=MetricType.CPU_USAGE.value,
                    value=cpu_percent,
                    unit="percent",
                    metadata={"process_id": process.pid}
                ))
            
            # Monitor memory usage
            if self.monitor_memory:
                memory_info = process.memory_info()
                
                self.harness.record_metric(PerformanceMetric(
                    name=MetricType.MEMORY_USAGE.value,
                    value=memory_info.rss / (1024 * 1024),  # Convert to MB
                    unit="MB",
                    metadata={"process_id": process.pid}
                ))
            
            # Sleep for interval
            time.sleep(self.interval)


class LoadGenerator:
    """
    Generator for load testing.
    """
    
    def __init__(
        self,
        harness: PerformanceHarness,
        target: Callable,
        concurrency: int = 1,
        duration: float = 60.0,
        ramp_up: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize load generator.
        
        Args:
            harness: Performance harness
            target: Target function to call
            concurrency: Number of concurrent users
            duration: Test duration in seconds
            ramp_up: Ramp-up time in seconds
            metadata: Optional metadata
        """
        self.harness = harness
        self.target = target
        self.concurrency = concurrency
        self.duration = duration
        self.ramp_up = ramp_up
        self.metadata = metadata or {}
        self.running = False
        self.tasks = []
        self.start_time = None
        self.end_time = None
        self.request_count = 0
    
    async def start(self):
        """Start load generation."""
        if self.running:
            return
        
        self.running = True
        self.start_time = time.time()
        self.request_count = 0
        
        # Create tasks
        self.tasks = []
        
        for i in range(self.concurrency):
            # Calculate delay for ramp-up
            if self.ramp_up > 0:
                delay = (i / self.concurrency) * self.ramp_up
            else:
                delay = 0
            
            # Create task
            task = asyncio.create_task(self._run_user(i, delay))
            self.tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*self.tasks)
        
        self.end_time = time.time()
        self.running = False
        
        # Calculate throughput
        test_duration = self.end_time - self.start_time
        throughput = self.request_count / test_duration
        
        # Record throughput metric
        self.harness.record_metric(PerformanceMetric(
            name=MetricType.THROUGHPUT.value,
            value=throughput,
            unit="requests/second",
            metadata={
                "concurrency": self.concurrency,
                "duration": test_duration,
                "request_count": self.request_count
            }
        ))
    
    async def _run_user(self, user_id: int, delay: float):
        """
        Run a simulated user.
        
        Args:
            user_id: User ID
            delay: Delay before starting
        """
        # Wait for delay
        if delay > 0:
            await asyncio.sleep(delay)
        
        # Calculate end time
        end_time = self.start_time + self.duration
        
        # Run until end time
        while time.time() < end_time and self.running:
            # Call target function
            start_time = time.time()
            
            try:
                if asyncio.iscoroutinefunction(self.target):
                    result = await self.target()
                else:
                    result = self.target()
                
                success = True
            except Exception as e:
                result = str(e)
                success = False
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Record response time metric
            self.harness.record_metric(PerformanceMetric(
                name=MetricType.RESPONSE_TIME.value,
                value=response_time,
                unit="seconds",
                metadata={
                    "user_id": user_id,
                    "success": success,
                    "result": str(result)[:100]  # Truncate result
                }
            ))
            
            # Increment request count
            self.request_count += 1
    
    def stop(self):
        """Stop load generation."""
        self.running = False


# Example usage
if __name__ == "__main__":
    # Create performance harness
    harness = PerformanceHarness()
    
    # Use timing context
    with TimingContext(harness, "example_operation"):
        # Simulate operation
        time.sleep(0.1)
    
    # Get metrics
    metrics = harness.get_metrics()
    
    # Print metrics
    for metric in metrics:
        print(f"{metric.name}: {metric.value} {metric.unit}")
