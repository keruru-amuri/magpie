"""
CI/CD configuration for the MAGPIE platform.

This module provides utilities for configuring CI/CD pipelines.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from datetime import datetime
from pathlib import Path

from tests.framework.ci_cd.pipeline import TestType, TestStatus, TestSuite, TestPipeline

# Configure logging
logger = logging.getLogger(__name__)


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
    
    def create_pipeline(self, output_dir: Optional[Union[str, Path]] = None) -> TestPipeline:
        """
        Create a test pipeline from configuration.
        
        Args:
            output_dir: Optional output directory
            
        Returns:
            Test pipeline
        """
        # Create pipeline
        pipeline = TestPipeline(name=self.name, output_dir=output_dir)
        
        # Add test suites
        for name, suite_config in self.config["test_suites"].items():
            suite = TestSuite(
                name=name,
                type=TestType(suite_config["type"]),
                command=suite_config["command"],
                path=suite_config["path"],
                timeout=suite_config["timeout"],
                metadata=suite_config["metadata"]
            )
            
            pipeline.add_suite(suite)
        
        return pipeline


def create_default_config() -> CIConfig:
    """
    Create default CI configuration.
    
    Returns:
        CI configuration
    """
    # Create configuration
    config = CIConfig("MAGPIE CI")
    
    # Add test suites
    config.add_test_suite(
        name="Unit Tests",
        type=TestType.UNIT,
        command="python -m pytest tests/unit",
        path="tests/unit",
        timeout=300
    )
    
    config.add_test_suite(
        name="Integration Tests",
        type=TestType.INTEGRATION,
        command="python -m pytest tests/integration",
        path="tests/integration",
        timeout=600
    )
    
    config.add_test_suite(
        name="Performance Tests",
        type=TestType.PERFORMANCE,
        command="python -m pytest tests/performance",
        path="tests/performance",
        timeout=1200
    )
    
    config.add_test_suite(
        name="Quality Tests",
        type=TestType.QUALITY,
        command="python -m pytest tests/quality",
        path="tests/quality",
        timeout=900
    )
    
    # Set thresholds
    config.set_threshold("pass_rate", 0.9)
    config.set_threshold("max_duration", 3600)
    
    return config


# Example usage
if __name__ == "__main__":
    # Create default configuration
    config = create_default_config()
    
    # Create pipeline
    pipeline = config.create_pipeline()
    
    # Run tests
    pipeline.run_all()
    
    # Get summary
    summary = pipeline.get_summary()
    print(f"Pass rate: {summary['pass_rate']:.2%}")
    
    # Save results
    pipeline.save_results()
