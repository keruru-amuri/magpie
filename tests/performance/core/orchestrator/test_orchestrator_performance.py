"""
Performance tests for the orchestrator.

This module contains performance tests for the orchestrator component.
"""
import pytest
import asyncio
import os
from typing import Dict, List, Any

from app.models.conversation import AgentType
from app.models.agent import ModelSize
from app.core.orchestrator.orchestrator import Orchestrator

from tests.framework.performance.harness import PerformanceHarness
from tests.framework.performance.benchmarks import (
    ResponseTimeBenchmark, ThroughputBenchmark,
    ModelComparisonBenchmark, ScalabilityBenchmark
)
from tests.framework.performance.visualization import MetricsVisualizer, ChartType
from tests.framework.performance.regression import RegressionDetector, BaselineManager
from tests.framework.utilities.input_simulator import InputSimulator

# Import fixtures
pytest_plugins = ["tests.conftest_agent", "tests.conftest_orchestrator"]


class TestOrchestratorPerformance:
    """
    Performance tests for the orchestrator.
    """
    
    @pytest.fixture
    def performance_harness(self):
        """
        Create performance harness.
        
        Returns:
            PerformanceHarness: Performance harness
        """
        return PerformanceHarness()
    
    @pytest.fixture
    def input_simulator(self):
        """
        Create input simulator.
        
        Returns:
            InputSimulator: Input simulator
        """
        return InputSimulator(seed=42)
    
    @pytest.fixture
    def metrics_visualizer(self, tmp_path):
        """
        Create metrics visualizer.
        
        Args:
            tmp_path: Temporary path
            
        Returns:
            MetricsVisualizer: Metrics visualizer
        """
        # Create output directory
        output_dir = tmp_path / "benchmark_results"
        os.makedirs(output_dir, exist_ok=True)
        
        return MetricsVisualizer(output_dir=output_dir)
    
    @pytest.fixture
    def regression_detector(self, tmp_path):
        """
        Create regression detector.
        
        Args:
            tmp_path: Temporary path
            
        Returns:
            RegressionDetector: Regression detector
        """
        # Create baseline directory
        baseline_dir = tmp_path / "benchmark_results" / "baselines"
        os.makedirs(baseline_dir, exist_ok=True)
        
        return RegressionDetector(baseline_dir=baseline_dir)
    
    @pytest.mark.asyncio
    async def test_orchestrator_response_time(
        self,
        orchestrator,
        performance_harness,
        input_simulator,
        metrics_visualizer
    ):
        """
        Test orchestrator response time.
        
        Args:
            orchestrator: Orchestrator
            performance_harness: Performance harness
            input_simulator: Input simulator
            metrics_visualizer: Metrics visualizer
        """
        # Create benchmark
        benchmark = ResponseTimeBenchmark(
            orchestrator=orchestrator,
            harness=performance_harness,
            input_simulator=input_simulator,
            agent_type=AgentType.DOCUMENTATION,
            num_requests=5
        )
        
        # Run benchmark
        results = await benchmark.run()
        
        # Set harness for visualizer
        metrics_visualizer.set_harness(performance_harness)
        
        # Save results
        benchmark.save_results(metrics_visualizer.output_dir)
        
        # Verify results
        assert "response_time_stats" in results
        assert results["response_time_stats"]["count"] == 5
        
        # Verify response time is reasonable (mock responses should be fast)
        assert results["response_time_stats"]["mean"] < 1.0  # Response time < 1 second
    
    @pytest.mark.asyncio
    async def test_orchestrator_model_comparison(
        self,
        orchestrator,
        performance_harness,
        input_simulator,
        metrics_visualizer
    ):
        """
        Test orchestrator model comparison.
        
        Args:
            orchestrator: Orchestrator
            performance_harness: Performance harness
            input_simulator: Input simulator
            metrics_visualizer: Metrics visualizer
        """
        # Create benchmark
        benchmark = ModelComparisonBenchmark(
            orchestrator=orchestrator,
            harness=performance_harness,
            input_simulator=input_simulator,
            agent_type=AgentType.DOCUMENTATION,
            model_sizes=[ModelSize.SMALL, ModelSize.MEDIUM, ModelSize.LARGE],
            num_requests=3
        )
        
        # Run benchmark
        results = await benchmark.run()
        
        # Set harness for visualizer
        metrics_visualizer.set_harness(performance_harness)
        
        # Save results
        benchmark.save_results(metrics_visualizer.output_dir)
        
        # Verify results
        assert "model_comparison" in results
        assert ModelSize.SMALL.value in results["model_comparison"]
        assert ModelSize.MEDIUM.value in results["model_comparison"]
        assert ModelSize.LARGE.value in results["model_comparison"]
        
        # Verify each model size has response time stats
        for model_size in [ModelSize.SMALL.value, ModelSize.MEDIUM.value, ModelSize.LARGE.value]:
            assert "response_time_stats" in results["model_comparison"][model_size]
            assert results["model_comparison"][model_size]["response_time_stats"]["count"] == 3
    
    @pytest.mark.asyncio
    async def test_orchestrator_throughput(
        self,
        orchestrator,
        performance_harness,
        input_simulator,
        metrics_visualizer
    ):
        """
        Test orchestrator throughput.
        
        Args:
            orchestrator: Orchestrator
            performance_harness: Performance harness
            input_simulator: Input simulator
            metrics_visualizer: Metrics visualizer
        """
        # Create benchmark
        benchmark = ThroughputBenchmark(
            orchestrator=orchestrator,
            harness=performance_harness,
            input_simulator=input_simulator,
            agent_type=AgentType.DOCUMENTATION,
            concurrency=3,
            duration=5.0
        )
        
        # Run benchmark
        results = await benchmark.run()
        
        # Set harness for visualizer
        metrics_visualizer.set_harness(performance_harness)
        
        # Save results
        benchmark.save_results(metrics_visualizer.output_dir)
        
        # Verify results
        assert "throughput" in results
        assert results["throughput"] > 0
        assert "response_time_stats" in results
        assert "cpu_usage_stats" in results
        assert "memory_usage_stats" in results
    
    @pytest.mark.asyncio
    async def test_orchestrator_scalability(
        self,
        orchestrator,
        performance_harness,
        input_simulator,
        metrics_visualizer
    ):
        """
        Test orchestrator scalability.
        
        Args:
            orchestrator: Orchestrator
            performance_harness: Performance harness
            input_simulator: Input simulator
            metrics_visualizer: Metrics visualizer
        """
        # Create benchmark
        benchmark = ScalabilityBenchmark(
            orchestrator=orchestrator,
            harness=performance_harness,
            input_simulator=input_simulator,
            agent_type=AgentType.DOCUMENTATION,
            concurrency_levels=[1, 2, 3],
            duration_per_level=3.0
        )
        
        # Run benchmark
        results = await benchmark.run()
        
        # Set harness for visualizer
        metrics_visualizer.set_harness(performance_harness)
        
        # Save results
        benchmark.save_results(metrics_visualizer.output_dir)
        
        # Verify results
        assert "scalability" in results
        assert 1 in results["scalability"]
        assert 2 in results["scalability"]
        assert 3 in results["scalability"]
        
        # Verify each concurrency level has throughput and response time stats
        for concurrency in [1, 2, 3]:
            assert "throughput" in results["scalability"][concurrency]
            assert "response_time_stats" in results["scalability"][concurrency]
            assert "cpu_usage_stats" in results["scalability"][concurrency]
            assert "memory_usage_stats" in results["scalability"][concurrency]
    
    @pytest.mark.asyncio
    async def test_orchestrator_regression_detection(
        self,
        orchestrator,
        performance_harness,
        input_simulator,
        regression_detector
    ):
        """
        Test orchestrator regression detection.
        
        Args:
            orchestrator: Orchestrator
            performance_harness: Performance harness
            input_simulator: Input simulator
            regression_detector: Regression detector
        """
        # Create benchmark
        benchmark = ResponseTimeBenchmark(
            orchestrator=orchestrator,
            harness=performance_harness,
            input_simulator=input_simulator,
            agent_type=AgentType.DOCUMENTATION,
            num_requests=5
        )
        
        # Run benchmark
        await benchmark.run()
        
        # Save baseline
        regression_detector.save_baseline("response_time_baseline", performance_harness)
        
        # Create new harness
        new_harness = PerformanceHarness()
        
        # Create benchmark with new harness
        new_benchmark = ResponseTimeBenchmark(
            orchestrator=orchestrator,
            harness=new_harness,
            input_simulator=input_simulator,
            agent_type=AgentType.DOCUMENTATION,
            num_requests=5
        )
        
        # Run benchmark
        await new_benchmark.run()
        
        # Detect regression
        results = regression_detector.detect_regression(
            "response_time_baseline",
            new_harness
        )
        
        # Verify results
        assert "regression_detected" in results
        assert "metrics" in results
        assert len(results["metrics"]) > 0
