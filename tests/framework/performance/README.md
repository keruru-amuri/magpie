# MAGPIE Performance Testing Framework

This directory contains the performance testing framework for the MAGPIE platform, designed to measure response times, throughput, and resource usage.

## Directory Structure

- `harness.py`: Performance test harness for measuring metrics
- `benchmarks.py`: Predefined benchmark scenarios
- `visualization.py`: Visualization tools for performance metrics
- `regression.py`: Performance regression detection utilities

## Performance Harness

The performance harness (`harness.py`) provides utilities for measuring performance metrics:

```python
from tests.framework.performance.harness import (
    PerformanceHarness, TimingContext, AsyncTimingContext,
    ResourceMonitor, LoadGenerator, MetricType
)

# Create performance harness
harness = PerformanceHarness()

# Use timing context
with TimingContext(harness, "example_operation"):
    # Simulate operation
    time.sleep(0.1)

# Use async timing context
async with AsyncTimingContext(harness, "async_operation"):
    # Simulate async operation
    await asyncio.sleep(0.1)

# Get metrics
metrics = harness.get_metrics()

# Get metric statistics
response_time_stats = harness.get_metric_statistics(
    name=MetricType.RESPONSE_TIME.value
)
```

## Benchmark Scenarios

The benchmark scenarios module (`benchmarks.py`) provides predefined benchmark scenarios:

```python
from tests.framework.performance.benchmarks import (
    ResponseTimeBenchmark, ThroughputBenchmark,
    ModelComparisonBenchmark, ScalabilityBenchmark
)

# Create response time benchmark
response_time_benchmark = ResponseTimeBenchmark(
    orchestrator=orchestrator,
    agent_type=AgentType.DOCUMENTATION,
    num_requests=10
)

# Run benchmark
await response_time_benchmark.run()

# Save results
response_time_benchmark.save_results("benchmark_results")
```

## Visualization Tools

The visualization tools module (`visualization.py`) provides utilities for visualizing performance metrics:

```python
from tests.framework.performance.visualization import (
    MetricsVisualizer, ChartType
)

# Create visualizer
visualizer = MetricsVisualizer()

# Set harness
visualizer.set_harness(harness)

# Plot metrics
visualizer.plot_metric_over_time(
    metric_name=MetricType.RESPONSE_TIME.value,
    title="Response Time Over Time",
    filename="response_time_over_time.png"
)

visualizer.plot_metric_distribution(
    metric_name=MetricType.RESPONSE_TIME.value,
    chart_type=ChartType.HISTOGRAM,
    title="Response Time Distribution",
    filename="response_time_distribution.png"
)

visualizer.plot_metric_comparison(
    metric_name=MetricType.RESPONSE_TIME.value,
    compare_by="model_size",
    chart_type=ChartType.BAR,
    title="Response Time by Model Size",
    filename="response_time_by_model_size.png"
)
```

## Regression Detection

The regression detection module (`regression.py`) provides utilities for detecting performance regressions:

```python
from tests.framework.performance.regression import (
    RegressionDetector, BaselineManager
)

# Create regression detector
detector = RegressionDetector()

# Save baseline
detector.save_baseline("baseline1", harness)

# Detect regression
results = detector.detect_regression("baseline1", new_harness)

# Create baseline manager
manager = BaselineManager()

# List baselines
baselines = manager.list_baselines()

# Compare baselines
comparison = manager.compare_baselines("baseline1", "baseline2")
```

## Writing Performance Tests

When writing performance tests using this framework, follow these guidelines:

1. Create a performance harness to collect metrics
2. Use timing contexts to measure operation durations
3. Use benchmark scenarios for standard performance tests
4. Use visualization tools to analyze results
5. Use regression detection to compare against baselines

Example test:

```python
import pytest
from tests.framework.performance.harness import PerformanceHarness
from tests.framework.performance.benchmarks import ResponseTimeBenchmark

class TestOrchestratorPerformance:
    @pytest.fixture
    def performance_harness(self):
        return PerformanceHarness()
    
    @pytest.mark.asyncio
    async def test_orchestrator_response_time(
        self, orchestrator, performance_harness
    ):
        # Create benchmark
        benchmark = ResponseTimeBenchmark(
            orchestrator=orchestrator,
            harness=performance_harness,
            agent_type=AgentType.DOCUMENTATION,
            num_requests=5
        )
        
        # Run benchmark
        results = await benchmark.run()
        
        # Verify results
        assert results["response_time_stats"]["mean"] < 1.0  # Response time < 1 second
        assert results["response_time_stats"]["p95"] < 2.0   # 95th percentile < 2 seconds
```

## Running Performance Tests

To run performance tests using this framework:

```bash
# Run all performance tests
python -m pytest tests/performance/

# Run specific test file
python -m pytest tests/performance/core/orchestrator/test_orchestrator_performance.py

# Run specific test class
python -m pytest tests/performance/core/orchestrator/test_orchestrator_performance.py::TestOrchestratorPerformance

# Run specific test method
python -m pytest tests/performance/core/orchestrator/test_orchestrator_performance.py::TestOrchestratorPerformance::test_orchestrator_response_time
```
