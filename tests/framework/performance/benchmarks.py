"""
Benchmark scenarios for performance testing.

This module provides predefined benchmark scenarios for performance testing.
"""
import time
import logging
import asyncio
import uuid
import json
import os
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
from datetime import datetime
from pathlib import Path

from app.models.conversation import AgentType
from app.models.agent import ModelSize
from app.models.orchestrator import OrchestratorRequest

from tests.framework.performance.harness import (
    PerformanceHarness, TimingContext, AsyncTimingContext,
    ResourceMonitor, LoadGenerator, MetricType, PerformanceMetric
)
from tests.framework.utilities.input_simulator import InputSimulator

# Configure logging
logger = logging.getLogger(__name__)


class BenchmarkType(Enum):
    """Enum for benchmark types."""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    SCALABILITY = "scalability"
    RESOURCE_USAGE = "resource_usage"
    MODEL_COMPARISON = "model_comparison"


class BenchmarkScenario:
    """
    Base class for benchmark scenarios.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        harness: Optional[PerformanceHarness] = None,
        input_simulator: Optional[InputSimulator] = None
    ):
        """
        Initialize a benchmark scenario.
        
        Args:
            name: Scenario name
            description: Scenario description
            harness: Optional performance harness
            input_simulator: Optional input simulator
        """
        self.name = name
        self.description = description
        self.harness = harness or PerformanceHarness()
        self.input_simulator = input_simulator or InputSimulator()
        self.parameters = {}
        self.results = {}
    
    async def setup(self):
        """Set up the benchmark."""
        pass
    
    async def run(self):
        """Run the benchmark."""
        raise NotImplementedError("Subclasses must implement run()")
    
    async def teardown(self):
        """Tear down the benchmark."""
        pass
    
    def set_parameter(self, key: str, value: Any):
        """
        Set a benchmark parameter.
        
        Args:
            key: Parameter key
            value: Parameter value
        """
        self.parameters[key] = value
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """
        Get a benchmark parameter.
        
        Args:
            key: Parameter key
            default: Default value if parameter not found
            
        Returns:
            Parameter value
        """
        return self.parameters.get(key, default)
    
    def add_result(self, key: str, value: Any):
        """
        Add a benchmark result.
        
        Args:
            key: Result key
            value: Result value
        """
        self.results[key] = value
    
    def get_result(self, key: str) -> Any:
        """
        Get a benchmark result.
        
        Args:
            key: Result key
            
        Returns:
            Result value
        """
        return self.results.get(key)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "results": {k: str(v) for k, v in self.results.items()},
            "metrics": self.harness.to_dict()
        }
    
    def save_results(self, output_dir: Union[str, Path], filename: Optional[str] = None):
        """
        Save benchmark results to file.
        
        Args:
            output_dir: Output directory
            filename: Optional filename
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.name.lower().replace(' ', '_')}_{timestamp}.json"
        
        # Create output path
        output_path = Path(output_dir) / filename
        
        # Save results
        with open(output_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        
        logger.info(f"Benchmark results saved to {output_path}")


class ResponseTimeBenchmark(BenchmarkScenario):
    """
    Benchmark for measuring response times.
    """
    
    def __init__(
        self,
        orchestrator,
        agent_type: Optional[AgentType] = None,
        model_size: Optional[ModelSize] = None,
        num_requests: int = 10,
        **kwargs
    ):
        """
        Initialize response time benchmark.
        
        Args:
            orchestrator: Orchestrator instance
            agent_type: Optional agent type
            model_size: Optional model size
            num_requests: Number of requests to send
            **kwargs: Additional arguments
        """
        super().__init__(
            name="Response Time Benchmark",
            description="Benchmark for measuring response times",
            **kwargs
        )
        
        self.orchestrator = orchestrator
        self.agent_type = agent_type or AgentType.DOCUMENTATION
        self.model_size = model_size or ModelSize.MEDIUM
        self.num_requests = num_requests
        
        # Set parameters
        self.set_parameter("agent_type", self.agent_type.value)
        self.set_parameter("model_size", self.model_size.value)
        self.set_parameter("num_requests", self.num_requests)
    
    async def run(self):
        """Run the benchmark."""
        logger.info(f"Running response time benchmark with {self.num_requests} requests")
        
        # Generate queries
        queries = [
            self.input_simulator.generate_random_query(self.agent_type)
            for _ in range(self.num_requests)
        ]
        
        # Process queries
        response_times = []
        
        for i, query in enumerate(queries):
            # Create request
            request = OrchestratorRequest(
                query=query,
                conversation_id=str(uuid.uuid4()),
                metadata={
                    "agent_type": self.agent_type.value,
                    "model_size": self.model_size.value
                }
            )
            
            # Process request with timing
            async with AsyncTimingContext(
                self.harness,
                MetricType.RESPONSE_TIME.value,
                metadata={
                    "request_id": i,
                    "agent_type": self.agent_type.value,
                    "model_size": self.model_size.value
                }
            ):
                response = await self.orchestrator.process_request(request)
            
            # Record token count
            if hasattr(response, "token_count") and response.token_count:
                self.harness.record_metric(PerformanceMetric(
                    name=MetricType.TOKEN_COUNT.value,
                    value=response.token_count,
                    unit="tokens",
                    metadata={
                        "request_id": i,
                        "agent_type": self.agent_type.value,
                        "model_size": self.model_size.value
                    }
                ))
        
        # Calculate statistics
        response_time_stats = self.harness.get_metric_statistics(
            name=MetricType.RESPONSE_TIME.value
        )
        
        # Add results
        self.add_result("response_time_stats", response_time_stats)
        
        logger.info(f"Response time benchmark completed: {response_time_stats}")
        
        return response_time_stats


class ThroughputBenchmark(BenchmarkScenario):
    """
    Benchmark for measuring throughput.
    """
    
    def __init__(
        self,
        orchestrator,
        agent_type: Optional[AgentType] = None,
        model_size: Optional[ModelSize] = None,
        concurrency: int = 5,
        duration: float = 30.0,
        **kwargs
    ):
        """
        Initialize throughput benchmark.
        
        Args:
            orchestrator: Orchestrator instance
            agent_type: Optional agent type
            model_size: Optional model size
            concurrency: Number of concurrent users
            duration: Test duration in seconds
            **kwargs: Additional arguments
        """
        super().__init__(
            name="Throughput Benchmark",
            description="Benchmark for measuring throughput",
            **kwargs
        )
        
        self.orchestrator = orchestrator
        self.agent_type = agent_type or AgentType.DOCUMENTATION
        self.model_size = model_size or ModelSize.MEDIUM
        self.concurrency = concurrency
        self.duration = duration
        
        # Set parameters
        self.set_parameter("agent_type", self.agent_type.value)
        self.set_parameter("model_size", self.model_size.value)
        self.set_parameter("concurrency", self.concurrency)
        self.set_parameter("duration", self.duration)
    
    async def run(self):
        """Run the benchmark."""
        logger.info(f"Running throughput benchmark with {self.concurrency} concurrent users for {self.duration} seconds")
        
        # Create resource monitor
        monitor = ResourceMonitor(self.harness)
        
        # Start resource monitoring
        monitor.start()
        
        # Create load generator
        load_generator = LoadGenerator(
            harness=self.harness,
            target=self._process_request,
            concurrency=self.concurrency,
            duration=self.duration,
            metadata={
                "agent_type": self.agent_type.value,
                "model_size": self.model_size.value
            }
        )
        
        # Run load generator
        await load_generator.start()
        
        # Stop resource monitoring
        monitor.stop()
        
        # Calculate statistics
        throughput = self.harness.get_metrics(name=MetricType.THROUGHPUT.value)
        response_time_stats = self.harness.get_metric_statistics(
            name=MetricType.RESPONSE_TIME.value
        )
        cpu_usage_stats = self.harness.get_metric_statistics(
            name=MetricType.CPU_USAGE.value
        )
        memory_usage_stats = self.harness.get_metric_statistics(
            name=MetricType.MEMORY_USAGE.value
        )
        
        # Add results
        self.add_result("throughput", throughput[0].value if throughput else 0)
        self.add_result("response_time_stats", response_time_stats)
        self.add_result("cpu_usage_stats", cpu_usage_stats)
        self.add_result("memory_usage_stats", memory_usage_stats)
        
        logger.info(f"Throughput benchmark completed: {throughput[0].value if throughput else 0} requests/second")
        
        return {
            "throughput": throughput[0].value if throughput else 0,
            "response_time_stats": response_time_stats,
            "cpu_usage_stats": cpu_usage_stats,
            "memory_usage_stats": memory_usage_stats
        }
    
    async def _process_request(self):
        """Process a request for load testing."""
        # Generate query
        query = self.input_simulator.generate_random_query(self.agent_type)
        
        # Create request
        request = OrchestratorRequest(
            query=query,
            conversation_id=str(uuid.uuid4()),
            metadata={
                "agent_type": self.agent_type.value,
                "model_size": self.model_size.value
            }
        )
        
        # Process request
        response = await self.orchestrator.process_request(request)
        
        return response


class ModelComparisonBenchmark(BenchmarkScenario):
    """
    Benchmark for comparing different model sizes.
    """
    
    def __init__(
        self,
        orchestrator,
        agent_type: Optional[AgentType] = None,
        model_sizes: Optional[List[ModelSize]] = None,
        num_requests: int = 5,
        **kwargs
    ):
        """
        Initialize model comparison benchmark.
        
        Args:
            orchestrator: Orchestrator instance
            agent_type: Optional agent type
            model_sizes: Optional list of model sizes
            num_requests: Number of requests per model size
            **kwargs: Additional arguments
        """
        super().__init__(
            name="Model Comparison Benchmark",
            description="Benchmark for comparing different model sizes",
            **kwargs
        )
        
        self.orchestrator = orchestrator
        self.agent_type = agent_type or AgentType.DOCUMENTATION
        self.model_sizes = model_sizes or [
            ModelSize.SMALL,
            ModelSize.MEDIUM,
            ModelSize.LARGE
        ]
        self.num_requests = num_requests
        
        # Set parameters
        self.set_parameter("agent_type", self.agent_type.value)
        self.set_parameter("model_sizes", [size.value for size in self.model_sizes])
        self.set_parameter("num_requests", self.num_requests)
    
    async def run(self):
        """Run the benchmark."""
        logger.info(f"Running model comparison benchmark with {len(self.model_sizes)} model sizes")
        
        # Generate queries (use same queries for all model sizes)
        queries = [
            self.input_simulator.generate_random_query(self.agent_type)
            for _ in range(self.num_requests)
        ]
        
        # Process queries for each model size
        results = {}
        
        for model_size in self.model_sizes:
            logger.info(f"Testing model size: {model_size.value}")
            
            # Process queries
            for i, query in enumerate(queries):
                # Create request
                request = OrchestratorRequest(
                    query=query,
                    conversation_id=str(uuid.uuid4()),
                    metadata={
                        "agent_type": self.agent_type.value,
                        "model_size": model_size.value
                    }
                )
                
                # Process request with timing
                async with AsyncTimingContext(
                    self.harness,
                    MetricType.RESPONSE_TIME.value,
                    metadata={
                        "request_id": i,
                        "agent_type": self.agent_type.value,
                        "model_size": model_size.value
                    }
                ):
                    response = await self.orchestrator.process_request(request)
                
                # Record token count
                if hasattr(response, "token_count") and response.token_count:
                    self.harness.record_metric(PerformanceMetric(
                        name=MetricType.TOKEN_COUNT.value,
                        value=response.token_count,
                        unit="tokens",
                        metadata={
                            "request_id": i,
                            "agent_type": self.agent_type.value,
                            "model_size": model_size.value
                        }
                    ))
                    
                    # Calculate token rate
                    response_time = self.harness.get_metrics(
                        name=MetricType.RESPONSE_TIME.value
                    )[-1].value
                    
                    if response_time > 0:
                        token_rate = response.token_count / response_time
                        
                        self.harness.record_metric(PerformanceMetric(
                            name=MetricType.TOKEN_RATE.value,
                            value=token_rate,
                            unit="tokens/second",
                            metadata={
                                "request_id": i,
                                "agent_type": self.agent_type.value,
                                "model_size": model_size.value
                            }
                        ))
            
            # Calculate statistics for this model size
            response_time_stats = self.harness.get_metric_statistics(
                name=MetricType.RESPONSE_TIME.value,
                unit="seconds"
            )
            
            token_count_stats = self.harness.get_metric_statistics(
                name=MetricType.TOKEN_COUNT.value,
                unit="tokens"
            )
            
            token_rate_stats = self.harness.get_metric_statistics(
                name=MetricType.TOKEN_RATE.value,
                unit="tokens/second"
            )
            
            # Add results for this model size
            results[model_size.value] = {
                "response_time_stats": response_time_stats,
                "token_count_stats": token_count_stats,
                "token_rate_stats": token_rate_stats
            }
        
        # Add overall results
        self.add_result("model_comparison", results)
        
        logger.info(f"Model comparison benchmark completed")
        
        return results


class ScalabilityBenchmark(BenchmarkScenario):
    """
    Benchmark for testing scalability with increasing load.
    """
    
    def __init__(
        self,
        orchestrator,
        agent_type: Optional[AgentType] = None,
        model_size: Optional[ModelSize] = None,
        concurrency_levels: Optional[List[int]] = None,
        duration_per_level: float = 20.0,
        **kwargs
    ):
        """
        Initialize scalability benchmark.
        
        Args:
            orchestrator: Orchestrator instance
            agent_type: Optional agent type
            model_size: Optional model size
            concurrency_levels: Optional list of concurrency levels
            duration_per_level: Duration per concurrency level in seconds
            **kwargs: Additional arguments
        """
        super().__init__(
            name="Scalability Benchmark",
            description="Benchmark for testing scalability with increasing load",
            **kwargs
        )
        
        self.orchestrator = orchestrator
        self.agent_type = agent_type or AgentType.DOCUMENTATION
        self.model_size = model_size or ModelSize.MEDIUM
        self.concurrency_levels = concurrency_levels or [1, 2, 5, 10]
        self.duration_per_level = duration_per_level
        
        # Set parameters
        self.set_parameter("agent_type", self.agent_type.value)
        self.set_parameter("model_size", self.model_size.value)
        self.set_parameter("concurrency_levels", self.concurrency_levels)
        self.set_parameter("duration_per_level", self.duration_per_level)
    
    async def run(self):
        """Run the benchmark."""
        logger.info(f"Running scalability benchmark with {len(self.concurrency_levels)} concurrency levels")
        
        # Create resource monitor
        monitor = ResourceMonitor(self.harness)
        
        # Start resource monitoring
        monitor.start()
        
        # Test each concurrency level
        results = {}
        
        for concurrency in self.concurrency_levels:
            logger.info(f"Testing concurrency level: {concurrency}")
            
            # Clear metrics for this level
            self.harness.clear()
            
            # Create load generator
            load_generator = LoadGenerator(
                harness=self.harness,
                target=self._process_request,
                concurrency=concurrency,
                duration=self.duration_per_level,
                metadata={
                    "agent_type": self.agent_type.value,
                    "model_size": self.model_size.value,
                    "concurrency": concurrency
                }
            )
            
            # Run load generator
            await load_generator.start()
            
            # Calculate statistics for this concurrency level
            throughput = self.harness.get_metrics(name=MetricType.THROUGHPUT.value)
            response_time_stats = self.harness.get_metric_statistics(
                name=MetricType.RESPONSE_TIME.value
            )
            cpu_usage_stats = self.harness.get_metric_statistics(
                name=MetricType.CPU_USAGE.value
            )
            memory_usage_stats = self.harness.get_metric_statistics(
                name=MetricType.MEMORY_USAGE.value
            )
            
            # Add results for this concurrency level
            results[concurrency] = {
                "throughput": throughput[0].value if throughput else 0,
                "response_time_stats": response_time_stats,
                "cpu_usage_stats": cpu_usage_stats,
                "memory_usage_stats": memory_usage_stats
            }
        
        # Stop resource monitoring
        monitor.stop()
        
        # Add overall results
        self.add_result("scalability", results)
        
        logger.info(f"Scalability benchmark completed")
        
        return results
    
    async def _process_request(self):
        """Process a request for load testing."""
        # Generate query
        query = self.input_simulator.generate_random_query(self.agent_type)
        
        # Create request
        request = OrchestratorRequest(
            query=query,
            conversation_id=str(uuid.uuid4()),
            metadata={
                "agent_type": self.agent_type.value,
                "model_size": self.model_size.value
            }
        )
        
        # Process request
        response = await self.orchestrator.process_request(request)
        
        return response


# Example usage
if __name__ == "__main__":
    # This is just an example and won't run without an actual orchestrator
    from app.core.orchestrator.orchestrator import Orchestrator
    
    async def test_benchmarks():
        # Create orchestrator
        orchestrator = Orchestrator(None, None)
        
        # Create performance harness
        harness = PerformanceHarness()
        
        # Create input simulator
        input_simulator = InputSimulator()
        
        # Create response time benchmark
        response_time_benchmark = ResponseTimeBenchmark(
            orchestrator=orchestrator,
            harness=harness,
            input_simulator=input_simulator,
            num_requests=5
        )
        
        # Run response time benchmark
        await response_time_benchmark.run()
        
        # Save results
        response_time_benchmark.save_results("benchmark_results")
    
    # Run benchmarks
    asyncio.run(test_benchmarks())
