"""
Integration test runner for executing test scenarios.

This module provides utilities for running integration test scenarios.
"""
import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Callable, Type
from datetime import datetime
from pathlib import Path

from tests.framework.integration.environment import IntegrationTestEnvironment
from tests.framework.integration.harness import InteractionTracker
from tests.framework.integration.scenarios import IntegrationTestScenario

# Configure logging
logger = logging.getLogger(__name__)


class TestResult:
    """
    Model for test results.
    """
    
    def __init__(
        self,
        scenario_name: str,
        success: bool,
        duration: float,
        error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize test result.
        
        Args:
            scenario_name: Scenario name
            success: Whether the test was successful
            duration: Test duration in seconds
            error: Optional error
            details: Optional details
        """
        self.scenario_name = scenario_name
        self.success = success
        self.duration = duration
        self.error = error
        self.details = details or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "scenario_name": self.scenario_name,
            "success": self.success,
            "duration": self.duration,
            "error": str(self.error) if self.error else None,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class TestSuite:
    """
    Test suite for running multiple test scenarios.
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        environment: Optional[IntegrationTestEnvironment] = None
    ):
        """
        Initialize test suite.
        
        Args:
            name: Suite name
            description: Optional suite description
            environment: Optional integration test environment
        """
        self.name = name
        self.description = description or f"Test suite: {name}"
        self.environment = environment or IntegrationTestEnvironment()
        self.scenarios = []
        self.results = []
        self.start_time = None
        self.end_time = None
    
    def add_scenario(self, scenario: IntegrationTestScenario):
        """
        Add a scenario to the test suite.
        
        Args:
            scenario: Test scenario
        """
        self.scenarios.append(scenario)
    
    async def run_scenario(self, scenario: IntegrationTestScenario) -> TestResult:
        """
        Run a test scenario.
        
        Args:
            scenario: Test scenario
            
        Returns:
            Test result
        """
        logger.info(f"Running scenario: {scenario.name}")
        
        start_time = time.time()
        
        try:
            # Set up scenario
            await scenario.setup()
            
            # Run scenario
            result = await scenario.run()
            
            # Tear down scenario
            await scenario.teardown()
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Create test result
            test_result = TestResult(
                scenario_name=scenario.name,
                success=True,
                duration=duration,
                details={"result": result, "scenario": scenario.to_dict()}
            )
            
            logger.info(f"Scenario {scenario.name} completed successfully in {duration:.2f} seconds")
            
            return test_result
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Create test result
            test_result = TestResult(
                scenario_name=scenario.name,
                success=False,
                duration=duration,
                error=e,
                details={"scenario": scenario.to_dict()}
            )
            
            logger.error(f"Scenario {scenario.name} failed: {str(e)}")
            
            return test_result
    
    async def run(self, parallel: bool = False) -> List[TestResult]:
        """
        Run all test scenarios.
        
        Args:
            parallel: Whether to run scenarios in parallel
            
        Returns:
            List of test results
        """
        logger.info(f"Running test suite: {self.name}")
        
        self.start_time = datetime.now()
        self.results = []
        
        if parallel:
            # Run scenarios in parallel
            tasks = [self.run_scenario(scenario) for scenario in self.scenarios]
            self.results = await asyncio.gather(*tasks)
        else:
            # Run scenarios sequentially
            for scenario in self.scenarios:
                result = await self.run_scenario(scenario)
                self.results.append(result)
        
        self.end_time = datetime.now()
        
        # Log summary
        success_count = sum(1 for result in self.results if result.success)
        failure_count = len(self.results) - success_count
        
        logger.info(f"Test suite {self.name} completed: {success_count} passed, {failure_count} failed")
        
        return self.results
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "description": self.description,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else None,
            "scenario_count": len(self.scenarios),
            "success_count": sum(1 for result in self.results if result.success),
            "failure_count": sum(1 for result in self.results if not result.success),
            "results": [result.to_dict() for result in self.results]
        }
    
    def save_results(self, output_dir: Union[str, Path], filename: Optional[str] = None):
        """
        Save test results to file.
        
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
        
        logger.info(f"Test results saved to {output_path}")


class TestRunner:
    """
    Runner for executing test suites.
    """
    
    def __init__(
        self,
        environment: Optional[IntegrationTestEnvironment] = None,
        output_dir: Optional[Union[str, Path]] = None
    ):
        """
        Initialize test runner.
        
        Args:
            environment: Optional integration test environment
            output_dir: Optional output directory
        """
        self.environment = environment or IntegrationTestEnvironment()
        self.output_dir = output_dir or Path("test_results")
        self.suites = []
    
    def add_suite(self, suite: TestSuite):
        """
        Add a test suite.
        
        Args:
            suite: Test suite
        """
        self.suites.append(suite)
    
    def create_suite(
        self,
        name: str,
        description: Optional[str] = None
    ) -> TestSuite:
        """
        Create a new test suite.
        
        Args:
            name: Suite name
            description: Optional suite description
            
        Returns:
            Test suite
        """
        suite = TestSuite(
            name=name,
            description=description,
            environment=self.environment
        )
        
        self.add_suite(suite)
        
        return suite
    
    async def run_suite(self, suite: TestSuite, parallel: bool = False) -> List[TestResult]:
        """
        Run a test suite.
        
        Args:
            suite: Test suite
            parallel: Whether to run scenarios in parallel
            
        Returns:
            List of test results
        """
        results = await suite.run(parallel=parallel)
        
        # Save results
        suite.save_results(self.output_dir)
        
        return results
    
    async def run_all(self, parallel_suites: bool = False, parallel_scenarios: bool = False) -> Dict[str, List[TestResult]]:
        """
        Run all test suites.
        
        Args:
            parallel_suites: Whether to run suites in parallel
            parallel_scenarios: Whether to run scenarios in parallel
            
        Returns:
            Dictionary of suite names to test results
        """
        logger.info(f"Running {len(self.suites)} test suites")
        
        results = {}
        
        if parallel_suites:
            # Run suites in parallel
            async def run_suite_wrapper(suite):
                suite_results = await self.run_suite(suite, parallel=parallel_scenarios)
                return suite.name, suite_results
            
            tasks = [run_suite_wrapper(suite) for suite in self.suites]
            suite_results = await asyncio.gather(*tasks)
            
            # Convert to dictionary
            results = dict(suite_results)
        else:
            # Run suites sequentially
            for suite in self.suites:
                suite_results = await self.run_suite(suite, parallel=parallel_scenarios)
                results[suite.name] = suite_results
        
        return results
    
    def cleanup(self):
        """Clean up the test environment."""
        self.environment.cleanup()


# Example usage
if __name__ == "__main__":
    # This is just an example and won't run without actual scenarios
    from tests.framework.integration.scenarios import SimpleQueryScenario
    
    async def test_runner():
        # Create test runner
        runner = TestRunner()
        
        # Create test suite
        suite = runner.create_suite("Example Suite", "Example test suite")
        
        # Add scenarios
        # suite.add_scenario(SimpleQueryScenario(...))
        
        # Run test suite
        results = await runner.run_suite(suite)
        
        # Clean up
        runner.cleanup()
    
    # Run test runner
    asyncio.run(test_runner())
