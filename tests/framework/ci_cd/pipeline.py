"""
CI/CD pipeline integration for the MAGPIE platform.

This module provides utilities for integrating tests with CI/CD pipelines.
"""
import os
import json
import logging
import subprocess
import time
from typing import Dict, List, Any, Optional, Union, Set
from enum import Enum
from datetime import datetime
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class TestType(Enum):
    """Enum for test types."""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    SECURITY = "security"


class TestStatus(Enum):
    """Enum for test status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestResult:
    """
    Model for test results.
    """
    
    def __init__(
        self,
        name: str,
        type: TestType,
        status: TestStatus,
        duration: float,
        output: str,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize test result.
        
        Args:
            name: Test name
            type: Test type
            status: Test status
            duration: Test duration in seconds
            output: Test output
            error: Optional error message
            metadata: Optional metadata
        """
        self.name = name
        self.type = type
        self.status = status
        self.duration = duration
        self.output = output
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "type": self.type.value,
            "status": self.status.value,
            "duration": self.duration,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class TestSuite:
    """
    Model for test suites.
    """
    
    def __init__(
        self,
        name: str,
        type: TestType,
        command: str,
        path: str,
        timeout: int = 300,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize test suite.
        
        Args:
            name: Test suite name
            type: Test type
            command: Test command
            path: Test path
            timeout: Test timeout in seconds
            metadata: Optional metadata
        """
        self.name = name
        self.type = type
        self.command = command
        self.path = path
        self.timeout = timeout
        self.metadata = metadata or {}
        self.results = []
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "type": self.type.value,
            "command": self.command,
            "path": self.path,
            "timeout": self.timeout,
            "metadata": self.metadata,
            "results": [result.to_dict() for result in self.results]
        }


class TestPipeline:
    """
    Pipeline for running tests in CI/CD.
    """
    
    def __init__(
        self,
        name: str,
        output_dir: Optional[Union[str, Path]] = None
    ):
        """
        Initialize test pipeline.
        
        Args:
            name: Pipeline name
            output_dir: Optional output directory
        """
        self.name = name
        self.output_dir = output_dir or Path("test_results")
        self.suites = []
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
    
    def add_suite(self, suite: TestSuite):
        """
        Add a test suite.
        
        Args:
            suite: Test suite
        """
        self.suites.append(suite)
    
    def run_suite(self, suite: TestSuite) -> List[TestResult]:
        """
        Run a test suite.
        
        Args:
            suite: Test suite
            
        Returns:
            List of test results
        """
        logger.info(f"Running test suite: {suite.name}")
        
        # Start time
        start_time = time.time()
        
        try:
            # Run command
            process = subprocess.Popen(
                suite.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for process to complete
            try:
                stdout, stderr = process.communicate(timeout=suite.timeout)
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Determine status
                if process.returncode == 0:
                    status = TestStatus.PASSED
                    error = None
                else:
                    status = TestStatus.FAILED
                    error = stderr
                
                # Create result
                result = TestResult(
                    name=suite.name,
                    type=suite.type,
                    status=status,
                    duration=duration,
                    output=stdout,
                    error=error,
                    metadata=suite.metadata
                )
                
                # Add result to suite
                suite.results.append(result)
                
                logger.info(f"Test suite {suite.name} completed with status: {status.value}")
                
                return [result]
            except subprocess.TimeoutExpired:
                # Kill process
                process.kill()
                stdout, stderr = process.communicate()
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Create result
                result = TestResult(
                    name=suite.name,
                    type=suite.type,
                    status=TestStatus.ERROR,
                    duration=duration,
                    output=stdout,
                    error=f"Timeout after {suite.timeout} seconds",
                    metadata=suite.metadata
                )
                
                # Add result to suite
                suite.results.append(result)
                
                logger.error(f"Test suite {suite.name} timed out after {suite.timeout} seconds")
                
                return [result]
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Create result
            result = TestResult(
                name=suite.name,
                type=suite.type,
                status=TestStatus.ERROR,
                duration=duration,
                output="",
                error=str(e),
                metadata=suite.metadata
            )
            
            # Add result to suite
            suite.results.append(result)
            
            logger.error(f"Error running test suite {suite.name}: {str(e)}")
            
            return [result]
    
    def run_all(self, types: Optional[List[TestType]] = None) -> Dict[str, List[TestResult]]:
        """
        Run all test suites.
        
        Args:
            types: Optional list of test types to run
            
        Returns:
            Dictionary of suite names to test results
        """
        results = {}
        
        for suite in self.suites:
            # Skip if type not in types
            if types and suite.type not in types:
                continue
            
            # Run suite
            suite_results = self.run_suite(suite)
            
            # Add to results
            results[suite.name] = suite_results
        
        return results
    
    def get_results(
        self,
        type: Optional[TestType] = None,
        status: Optional[TestStatus] = None
    ) -> List[TestResult]:
        """
        Get test results.
        
        Args:
            type: Optional test type filter
            status: Optional test status filter
            
        Returns:
            List of test results
        """
        results = []
        
        for suite in self.suites:
            # Skip if type doesn't match
            if type and suite.type != type:
                continue
            
            for result in suite.results:
                # Skip if status doesn't match
                if status and result.status != status:
                    continue
                
                results.append(result)
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get test summary.
        
        Returns:
            Dictionary with test summary
        """
        # Count results by status
        status_counts = {status.value: 0 for status in TestStatus}
        
        for suite in self.suites:
            for result in suite.results:
                status_counts[result.status.value] += 1
        
        # Calculate total duration
        total_duration = sum(
            result.duration
            for suite in self.suites
            for result in suite.results
        )
        
        # Calculate pass rate
        total_results = sum(status_counts.values())
        pass_rate = status_counts[TestStatus.PASSED.value] / total_results if total_results > 0 else 0
        
        return {
            "name": self.name,
            "total_suites": len(self.suites),
            "total_results": total_results,
            "status_counts": status_counts,
            "pass_rate": pass_rate,
            "total_duration": total_duration
        }
    
    def save_results(self, filename: Optional[str] = None):
        """
        Save test results to file.
        
        Args:
            filename: Optional filename
        """
        # Generate filename
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.name.lower().replace(' ', '_')}_{timestamp}.json"
        
        # Create output path
        output_path = Path(self.output_dir) / filename
        
        # Save results
        with open(output_path, "w") as f:
            json.dump({
                "name": self.name,
                "timestamp": datetime.now().isoformat(),
                "summary": self.get_summary(),
                "suites": [suite.to_dict() for suite in self.suites]
            }, f, indent=2)
        
        logger.info(f"Test results saved to {output_path}")


class TestSelector:
    """
    Selector for optimizing test selection in CI/CD.
    """
    
    def __init__(
        self,
        base_dir: Optional[Union[str, Path]] = None,
        history_file: Optional[Union[str, Path]] = None
    ):
        """
        Initialize test selector.
        
        Args:
            base_dir: Optional base directory
            history_file: Optional history file
        """
        self.base_dir = base_dir or Path(".")
        self.history_file = history_file or Path("test_history.json")
        self.history = self._load_history()
    
    def _load_history(self) -> Dict[str, Any]:
        """
        Load test history.
        
        Returns:
            Test history
        """
        if not os.path.exists(self.history_file):
            return {
                "test_runs": [],
                "file_dependencies": {},
                "test_durations": {}
            }
        
        try:
            with open(self.history_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading test history: {str(e)}")
            return {
                "test_runs": [],
                "file_dependencies": {},
                "test_durations": {}
            }
    
    def _save_history(self):
        """Save test history."""
        try:
            with open(self.history_file, "w") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving test history: {str(e)}")
    
    def update_history(
        self,
        test_name: str,
        duration: float,
        status: TestStatus,
        dependencies: Optional[List[str]] = None
    ):
        """
        Update test history.
        
        Args:
            test_name: Test name
            duration: Test duration
            status: Test status
            dependencies: Optional list of file dependencies
        """
        # Update test durations
        self.history["test_durations"][test_name] = duration
        
        # Update file dependencies
        if dependencies:
            for dependency in dependencies:
                if dependency not in self.history["file_dependencies"]:
                    self.history["file_dependencies"][dependency] = []
                
                if test_name not in self.history["file_dependencies"][dependency]:
                    self.history["file_dependencies"][dependency].append(test_name)
        
        # Add test run
        self.history["test_runs"].append({
            "test_name": test_name,
            "duration": duration,
            "status": status.value,
            "timestamp": datetime.now().isoformat()
        })
        
        # Save history
        self._save_history()
    
    def select_tests(
        self,
        changed_files: List[str],
        all_tests: List[str],
        max_duration: Optional[float] = None
    ) -> List[str]:
        """
        Select tests to run based on changed files.
        
        Args:
            changed_files: List of changed files
            all_tests: List of all tests
            max_duration: Optional maximum duration
            
        Returns:
            List of tests to run
        """
        # If no changed files, run all tests
        if not changed_files:
            return all_tests
        
        # Get tests affected by changed files
        affected_tests = set()
        
        for file in changed_files:
            if file in self.history["file_dependencies"]:
                affected_tests.update(self.history["file_dependencies"][file])
        
        # If no affected tests, run all tests
        if not affected_tests:
            return all_tests
        
        # Filter affected tests to those in all_tests
        affected_tests = [test for test in affected_tests if test in all_tests]
        
        # If max_duration is specified, prioritize tests
        if max_duration is not None:
            # Sort tests by duration (ascending)
            affected_tests.sort(
                key=lambda test: self.history["test_durations"].get(test, float("inf"))
            )
            
            # Select tests up to max_duration
            selected_tests = []
            total_duration = 0
            
            for test in affected_tests:
                duration = self.history["test_durations"].get(test, 0)
                
                if total_duration + duration <= max_duration:
                    selected_tests.append(test)
                    total_duration += duration
                else:
                    break
            
            return selected_tests
        
        return affected_tests


class CIConfig:
    """
    Configuration for CI/CD integration.
    """
    
    def __init__(
        self,
        name: str,
        config_file: Optional[Union[str, Path]] = None
    ):
        """
        Initialize CI configuration.
        
        Args:
            name: Configuration name
            config_file: Optional configuration file
        """
        self.name = name
        self.config_file = config_file or Path("ci_config.json")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration.
        
        Returns:
            Configuration dictionary
        """
        if not os.path.exists(self.config_file):
            return {
                "name": self.name,
                "test_suites": {},
                "notifications": {},
                "thresholds": {
                    "pass_rate": 0.8,
                    "max_duration": 3600
                }
            }
        
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading CI configuration: {str(e)}")
            return {
                "name": self.name,
                "test_suites": {},
                "notifications": {},
                "thresholds": {
                    "pass_rate": 0.8,
                    "max_duration": 3600
                }
            }
    
    def _save_config(self):
        """Save configuration."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving CI configuration: {str(e)}")
    
    def add_test_suite(
        self,
        name: str,
        type: TestType,
        command: str,
        path: str,
        timeout: int = 300,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a test suite.
        
        Args:
            name: Test suite name
            type: Test type
            command: Test command
            path: Test path
            timeout: Test timeout in seconds
            metadata: Optional metadata
        """
        self.config["test_suites"][name] = {
            "type": type.value,
            "command": command,
            "path": path,
            "timeout": timeout,
            "metadata": metadata or {}
        }
        
        self._save_config()
    
    def remove_test_suite(self, name: str):
        """
        Remove a test suite.
        
        Args:
            name: Test suite name
        """
        if name in self.config["test_suites"]:
            del self.config["test_suites"][name]
            self._save_config()
    
    def get_test_suites(self, type: Optional[TestType] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get test suites.
        
        Args:
            type: Optional test type filter
            
        Returns:
            Dictionary of test suites
        """
        if type:
            return {
                name: suite
                for name, suite in self.config["test_suites"].items()
                if suite["type"] == type.value
            }
        
        return self.config["test_suites"]
    
    def set_threshold(self, name: str, value: float):
        """
        Set a threshold.
        
        Args:
            name: Threshold name
            value: Threshold value
        """
        self.config["thresholds"][name] = value
        self._save_config()
    
    def get_threshold(self, name: str) -> Optional[float]:
        """
        Get a threshold.
        
        Args:
            name: Threshold name
            
        Returns:
            Threshold value
        """
        return self.config["thresholds"].get(name)
    
    def add_notification(
        self,
        name: str,
        type: str,
        config: Dict[str, Any]
    ):
        """
        Add a notification.
        
        Args:
            name: Notification name
            type: Notification type
            config: Notification configuration
        """
        self.config["notifications"][name] = {
            "type": type,
            "config": config
        }
        
        self._save_config()
    
    def remove_notification(self, name: str):
        """
        Remove a notification.
        
        Args:
            name: Notification name
        """
        if name in self.config["notifications"]:
            del self.config["notifications"][name]
            self._save_config()
    
    def get_notifications(self) -> Dict[str, Dict[str, Any]]:
        """
        Get notifications.
        
        Returns:
            Dictionary of notifications
        """
        return self.config["notifications"]


# Example usage
if __name__ == "__main__":
    # Create CI configuration
    ci_config = CIConfig("MAGPIE CI")
    
    # Add test suites
    ci_config.add_test_suite(
        name="Unit Tests",
        type=TestType.UNIT,
        command="python -m pytest tests/unit",
        path="tests/unit",
        timeout=300
    )
    
    ci_config.add_test_suite(
        name="Integration Tests",
        type=TestType.INTEGRATION,
        command="python -m pytest tests/integration",
        path="tests/integration",
        timeout=600
    )
    
    ci_config.add_test_suite(
        name="Performance Tests",
        type=TestType.PERFORMANCE,
        command="python -m pytest tests/performance",
        path="tests/performance",
        timeout=1200
    )
    
    ci_config.add_test_suite(
        name="Quality Tests",
        type=TestType.QUALITY,
        command="python -m pytest tests/quality",
        path="tests/quality",
        timeout=900
    )
    
    # Create test pipeline
    pipeline = TestPipeline("MAGPIE Tests")
    
    # Add test suites
    for name, suite_config in ci_config.get_test_suites().items():
        suite = TestSuite(
            name=name,
            type=TestType(suite_config["type"]),
            command=suite_config["command"],
            path=suite_config["path"],
            timeout=suite_config["timeout"],
            metadata=suite_config["metadata"]
        )
        
        pipeline.add_suite(suite)
    
    # Run tests
    pipeline.run_all()
    
    # Get summary
    summary = pipeline.get_summary()
    print(f"Pass rate: {summary['pass_rate']:.2%}")
    
    # Save results
    pipeline.save_results()
