"""
Performance regression detection utilities.

This module provides utilities for detecting performance regressions.
"""
import os
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
from datetime import datetime
from pathlib import Path

from tests.framework.performance.harness import PerformanceHarness, MetricType, PerformanceMetric

# Configure logging
logger = logging.getLogger(__name__)


class RegressionSeverity(Enum):
    """Enum for regression severity levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RegressionDetector:
    """
    Detector for performance regressions.
    """
    
    def __init__(
        self,
        baseline_dir: Optional[Union[str, Path]] = None,
        threshold_low: float = 0.1,
        threshold_medium: float = 0.2,
        threshold_high: float = 0.5,
        threshold_critical: float = 1.0
    ):
        """
        Initialize regression detector.
        
        Args:
            baseline_dir: Optional directory containing baseline metrics
            threshold_low: Threshold for low severity (10% by default)
            threshold_medium: Threshold for medium severity (20% by default)
            threshold_high: Threshold for high severity (50% by default)
            threshold_critical: Threshold for critical severity (100% by default)
        """
        self.baseline_dir = baseline_dir or Path("benchmark_results/baselines")
        self.threshold_low = threshold_low
        self.threshold_medium = threshold_medium
        self.threshold_high = threshold_high
        self.threshold_critical = threshold_critical
        self.baselines = {}
    
    def load_baseline(self, name: str, file_path: Optional[Union[str, Path]] = None):
        """
        Load baseline metrics from file.
        
        Args:
            name: Baseline name
            file_path: Optional path to baseline file (defaults to {baseline_dir}/{name}.json)
        """
        # Determine file path
        if file_path is None:
            file_path = Path(self.baseline_dir) / f"{name}.json"
        
        # Load baseline
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            # Store baseline
            self.baselines[name] = data
            
            logger.info(f"Loaded baseline {name} from {file_path}")
        except Exception as e:
            logger.warning(f"Error loading baseline {name} from {file_path}: {str(e)}")
    
    def save_baseline(
        self,
        name: str,
        harness: PerformanceHarness,
        file_path: Optional[Union[str, Path]] = None
    ):
        """
        Save baseline metrics to file.
        
        Args:
            name: Baseline name
            harness: Performance harness
            file_path: Optional path to baseline file (defaults to {baseline_dir}/{name}.json)
        """
        # Create baseline directory
        os.makedirs(self.baseline_dir, exist_ok=True)
        
        # Determine file path
        if file_path is None:
            file_path = Path(self.baseline_dir) / f"{name}.json"
        
        # Create baseline data
        baseline_data = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "metrics": harness.to_dict()
        }
        
        # Save baseline
        with open(file_path, "w") as f:
            json.dump(baseline_data, f, indent=2)
        
        # Store baseline
        self.baselines[name] = baseline_data
        
        logger.info(f"Saved baseline {name} to {file_path}")
    
    def detect_regression(
        self,
        baseline_name: str,
        harness: PerformanceHarness,
        metric_name: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect performance regression.
        
        Args:
            baseline_name: Baseline name
            harness: Performance harness
            metric_name: Optional metric name filter
            metadata_filters: Optional metadata filters
            
        Returns:
            Dictionary with regression detection results
        """
        # Check if baseline exists
        if baseline_name not in self.baselines:
            logger.warning(f"Baseline {baseline_name} not found")
            return {
                "baseline_name": baseline_name,
                "regression_detected": False,
                "error": "Baseline not found"
            }
        
        # Get baseline metrics
        baseline_metrics = self.baselines[baseline_name]["metrics"]["metrics"]
        
        # Filter baseline metrics
        if metric_name:
            baseline_metrics = [m for m in baseline_metrics if m["name"] == metric_name]
        
        if metadata_filters:
            filtered_metrics = []
            
            for metric in baseline_metrics:
                match = True
                
                for key, value in metadata_filters.items():
                    if key not in metric["metadata"] or metric["metadata"][key] != value:
                        match = False
                        break
                
                if match:
                    filtered_metrics.append(metric)
            
            baseline_metrics = filtered_metrics
        
        # Get current metrics
        current_metrics = harness.get_metrics(name=metric_name)
        
        # Filter current metrics
        if metadata_filters:
            filtered_metrics = []
            
            for metric in current_metrics:
                match = True
                
                for key, value in metadata_filters.items():
                    if key not in metric.metadata or metric.metadata[key] != value:
                        match = False
                        break
                
                if match:
                    filtered_metrics.append(metric)
            
            current_metrics = filtered_metrics
        
        # Group metrics by name and unit
        baseline_groups = {}
        for metric in baseline_metrics:
            key = f"{metric['name']}_{metric['unit']}"
            if key not in baseline_groups:
                baseline_groups[key] = []
            baseline_groups[key].append(metric["value"])
        
        current_groups = {}
        for metric in current_metrics:
            key = f"{metric.name}_{metric.unit}"
            if key not in current_groups:
                current_groups[key] = []
            current_groups[key].append(metric.value)
        
        # Compare metrics
        results = {
            "baseline_name": baseline_name,
            "regression_detected": False,
            "metrics": []
        }
        
        for key in current_groups:
            if key in baseline_groups:
                # Calculate statistics
                baseline_values = baseline_groups[key]
                current_values = current_groups[key]
                
                baseline_mean = np.mean(baseline_values)
                current_mean = np.mean(current_values)
                
                if baseline_mean > 0:
                    # Calculate change
                    change = (current_mean - baseline_mean) / baseline_mean
                    
                    # Determine if regression
                    is_regression = False
                    severity = RegressionSeverity.NONE
                    
                    # For response time, throughput, etc. where higher is worse
                    if key.startswith(f"{MetricType.RESPONSE_TIME.value}_") or key.startswith("cpu_usage_") or key.startswith("memory_usage_"):
                        if change > 0:
                            is_regression = True
                            
                            if change >= self.threshold_critical:
                                severity = RegressionSeverity.CRITICAL
                            elif change >= self.threshold_high:
                                severity = RegressionSeverity.HIGH
                            elif change >= self.threshold_medium:
                                severity = RegressionSeverity.MEDIUM
                            elif change >= self.threshold_low:
                                severity = RegressionSeverity.LOW
                    
                    # For throughput, token rate, etc. where lower is worse
                    elif key.startswith(f"{MetricType.THROUGHPUT.value}_") or key.startswith(f"{MetricType.TOKEN_RATE.value}_"):
                        if change < 0:
                            is_regression = True
                            change = -change  # Make positive for severity calculation
                            
                            if change >= self.threshold_critical:
                                severity = RegressionSeverity.CRITICAL
                            elif change >= self.threshold_high:
                                severity = RegressionSeverity.HIGH
                            elif change >= self.threshold_medium:
                                severity = RegressionSeverity.MEDIUM
                            elif change >= self.threshold_low:
                                severity = RegressionSeverity.LOW
                    
                    # Add to results
                    metric_result = {
                        "metric_key": key,
                        "baseline_mean": baseline_mean,
                        "current_mean": current_mean,
                        "change": change,
                        "is_regression": is_regression,
                        "severity": severity.value if is_regression else RegressionSeverity.NONE.value
                    }
                    
                    results["metrics"].append(metric_result)
                    
                    # Update overall result
                    if is_regression:
                        results["regression_detected"] = True
        
        return results


class BaselineManager:
    """
    Manager for performance baselines.
    """
    
    def __init__(
        self,
        baseline_dir: Optional[Union[str, Path]] = None
    ):
        """
        Initialize baseline manager.
        
        Args:
            baseline_dir: Optional directory containing baseline metrics
        """
        self.baseline_dir = baseline_dir or Path("benchmark_results/baselines")
        
        # Create baseline directory
        os.makedirs(self.baseline_dir, exist_ok=True)
    
    def list_baselines(self) -> List[str]:
        """
        List available baselines.
        
        Returns:
            List of baseline names
        """
        baselines = []
        
        for file_path in Path(self.baseline_dir).glob("*.json"):
            baselines.append(file_path.stem)
        
        return baselines
    
    def create_baseline(
        self,
        name: str,
        harness: PerformanceHarness,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Create a new baseline.
        
        Args:
            name: Baseline name
            harness: Performance harness
            description: Optional description
            metadata: Optional metadata
        """
        # Create baseline data
        baseline_data = {
            "name": name,
            "description": description or f"Baseline {name}",
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "metrics": harness.to_dict()
        }
        
        # Save baseline
        file_path = Path(self.baseline_dir) / f"{name}.json"
        
        with open(file_path, "w") as f:
            json.dump(baseline_data, f, indent=2)
        
        logger.info(f"Created baseline {name} at {file_path}")
    
    def load_baseline(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a baseline.
        
        Args:
            name: Baseline name
            
        Returns:
            Baseline data or None if not found
        """
        file_path = Path(self.baseline_dir) / f"{name}.json"
        
        if not file_path.exists():
            logger.warning(f"Baseline {name} not found")
            return None
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            return data
        except Exception as e:
            logger.warning(f"Error loading baseline {name}: {str(e)}")
            return None
    
    def delete_baseline(self, name: str) -> bool:
        """
        Delete a baseline.
        
        Args:
            name: Baseline name
            
        Returns:
            True if deleted, False otherwise
        """
        file_path = Path(self.baseline_dir) / f"{name}.json"
        
        if not file_path.exists():
            logger.warning(f"Baseline {name} not found")
            return False
        
        try:
            os.remove(file_path)
            logger.info(f"Deleted baseline {name}")
            return True
        except Exception as e:
            logger.warning(f"Error deleting baseline {name}: {str(e)}")
            return False
    
    def compare_baselines(
        self,
        baseline1: str,
        baseline2: str,
        metric_name: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compare two baselines.
        
        Args:
            baseline1: First baseline name
            baseline2: Second baseline name
            metric_name: Optional metric name filter
            metadata_filters: Optional metadata filters
            
        Returns:
            Dictionary with comparison results
        """
        # Load baselines
        data1 = self.load_baseline(baseline1)
        data2 = self.load_baseline(baseline2)
        
        if not data1 or not data2:
            return {
                "error": "One or both baselines not found"
            }
        
        # Get metrics
        metrics1 = data1["metrics"]["metrics"]
        metrics2 = data2["metrics"]["metrics"]
        
        # Filter metrics
        if metric_name:
            metrics1 = [m for m in metrics1 if m["name"] == metric_name]
            metrics2 = [m for m in metrics2 if m["name"] == metric_name]
        
        if metadata_filters:
            filtered_metrics1 = []
            filtered_metrics2 = []
            
            for metric in metrics1:
                match = True
                
                for key, value in metadata_filters.items():
                    if key not in metric["metadata"] or metric["metadata"][key] != value:
                        match = False
                        break
                
                if match:
                    filtered_metrics1.append(metric)
            
            for metric in metrics2:
                match = True
                
                for key, value in metadata_filters.items():
                    if key not in metric["metadata"] or metric["metadata"][key] != value:
                        match = False
                        break
                
                if match:
                    filtered_metrics2.append(metric)
            
            metrics1 = filtered_metrics1
            metrics2 = filtered_metrics2
        
        # Group metrics by name and unit
        groups1 = {}
        for metric in metrics1:
            key = f"{metric['name']}_{metric['unit']}"
            if key not in groups1:
                groups1[key] = []
            groups1[key].append(metric["value"])
        
        groups2 = {}
        for metric in metrics2:
            key = f"{metric['name']}_{metric['unit']}"
            if key not in groups2:
                groups2[key] = []
            groups2[key].append(metric["value"])
        
        # Compare metrics
        results = {
            "baseline1": baseline1,
            "baseline2": baseline2,
            "metrics": []
        }
        
        # Find all unique keys
        all_keys = set(groups1.keys()) | set(groups2.keys())
        
        for key in all_keys:
            if key in groups1 and key in groups2:
                # Calculate statistics
                values1 = groups1[key]
                values2 = groups2[key]
                
                mean1 = np.mean(values1)
                mean2 = np.mean(values2)
                
                if mean1 > 0:
                    # Calculate change
                    change = (mean2 - mean1) / mean1
                    
                    # Add to results
                    metric_result = {
                        "metric_key": key,
                        "baseline1_mean": mean1,
                        "baseline2_mean": mean2,
                        "change": change
                    }
                    
                    results["metrics"].append(metric_result)
            elif key in groups1:
                # Only in baseline1
                results["metrics"].append({
                    "metric_key": key,
                    "baseline1_mean": np.mean(groups1[key]),
                    "baseline2_mean": None,
                    "change": None
                })
            elif key in groups2:
                # Only in baseline2
                results["metrics"].append({
                    "metric_key": key,
                    "baseline1_mean": None,
                    "baseline2_mean": np.mean(groups2[key]),
                    "change": None
                })
        
        return results


# Example usage
if __name__ == "__main__":
    # Create regression detector
    detector = RegressionDetector()
    
    # Create baseline manager
    manager = BaselineManager()
    
    # List baselines
    baselines = manager.list_baselines()
    print(f"Available baselines: {baselines}")
