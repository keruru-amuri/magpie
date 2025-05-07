"""
Visualization tools for performance metrics.

This module provides utilities for visualizing performance metrics.
"""
import os
import json
import logging
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
from datetime import datetime
from pathlib import Path

from tests.framework.performance.harness import PerformanceHarness, MetricType

# Configure logging
logger = logging.getLogger(__name__)


class ChartType(Enum):
    """Enum for chart types."""
    LINE = "line"
    BAR = "bar"
    HISTOGRAM = "histogram"
    BOX = "box"
    SCATTER = "scatter"
    HEATMAP = "heatmap"


class MetricsVisualizer:
    """
    Visualizer for performance metrics.
    """
    
    def __init__(
        self,
        harness: Optional[PerformanceHarness] = None,
        output_dir: Optional[Union[str, Path]] = None
    ):
        """
        Initialize metrics visualizer.
        
        Args:
            harness: Optional performance harness
            output_dir: Optional output directory
        """
        self.harness = harness
        self.output_dir = output_dir or Path("benchmark_results")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
    
    def set_harness(self, harness: PerformanceHarness):
        """
        Set performance harness.
        
        Args:
            harness: Performance harness
        """
        self.harness = harness
    
    def load_metrics_from_file(self, file_path: Union[str, Path]):
        """
        Load metrics from file.
        
        Args:
            file_path: Path to metrics file
        """
        with open(file_path, "r") as f:
            data = json.load(f)
        
        # Create new harness
        self.harness = PerformanceHarness()
        
        # Load metrics
        for metric_data in data["metrics"]:
            # Create metric
            metric = {
                "name": metric_data["name"],
                "value": metric_data["value"],
                "unit": metric_data["unit"],
                "timestamp": datetime.fromisoformat(metric_data["timestamp"]),
                "metadata": metric_data["metadata"]
            }
            
            # Add metric to harness
            self.harness.metrics.append(metric)
        
        # Set start and end time
        self.harness.start_time = datetime.fromisoformat(data["start_time"])
        self.harness.end_time = datetime.fromisoformat(data["end_time"])
    
    def create_dataframe(
        self,
        metric_name: Optional[str] = None,
        unit: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Create DataFrame from metrics.
        
        Args:
            metric_name: Optional metric name filter
            unit: Optional unit filter
            metadata_filters: Optional metadata filters
            
        Returns:
            DataFrame containing metrics
        """
        if not self.harness:
            raise ValueError("No performance harness available")
        
        # Get metrics
        metrics = self.harness.get_metrics(name=metric_name, unit=unit)
        
        # Apply metadata filters
        if metadata_filters:
            filtered_metrics = []
            
            for metric in metrics:
                match = True
                
                for key, value in metadata_filters.items():
                    if key not in metric.metadata or metric.metadata[key] != value:
                        match = False
                        break
                
                if match:
                    filtered_metrics.append(metric)
            
            metrics = filtered_metrics
        
        # Create DataFrame
        data = []
        
        for metric in metrics:
            row = {
                "name": metric.name,
                "value": metric.value,
                "unit": metric.unit,
                "timestamp": metric.timestamp
            }
            
            # Add metadata
            for key, value in metric.metadata.items():
                row[f"metadata_{key}"] = value
            
            data.append(row)
        
        return pd.DataFrame(data)
    
    def plot_metric_over_time(
        self,
        metric_name: str,
        unit: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
        group_by: Optional[str] = None,
        title: Optional[str] = None,
        filename: Optional[str] = None
    ):
        """
        Plot metric values over time.
        
        Args:
            metric_name: Metric name
            unit: Optional unit filter
            metadata_filters: Optional metadata filters
            group_by: Optional metadata key to group by
            title: Optional chart title
            filename: Optional output filename
        """
        # Create DataFrame
        df = self.create_dataframe(
            metric_name=metric_name,
            unit=unit,
            metadata_filters=metadata_filters
        )
        
        if df.empty:
            logger.warning(f"No metrics found for {metric_name}")
            return
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Plot data
        if group_by and f"metadata_{group_by}" in df.columns:
            # Group by metadata key
            groups = df[f"metadata_{group_by}"].unique()
            
            for group in groups:
                group_df = df[df[f"metadata_{group_by}"] == group]
                plt.plot(
                    group_df["timestamp"],
                    group_df["value"],
                    marker="o",
                    linestyle="-",
                    label=str(group)
                )
            
            plt.legend(title=group_by)
        else:
            # Plot all data
            plt.plot(
                df["timestamp"],
                df["value"],
                marker="o",
                linestyle="-"
            )
        
        # Set labels
        plt.xlabel("Time")
        plt.ylabel(f"{metric_name} ({df['unit'].iloc[0]})")
        plt.title(title or f"{metric_name} over time")
        
        # Format x-axis
        plt.gcf().autofmt_xdate()
        
        # Save figure
        if filename:
            output_path = Path(self.output_dir) / filename
            plt.savefig(output_path)
            logger.info(f"Chart saved to {output_path}")
        
        # Show figure
        plt.tight_layout()
        plt.show()
    
    def plot_metric_distribution(
        self,
        metric_name: str,
        unit: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
        chart_type: ChartType = ChartType.HISTOGRAM,
        group_by: Optional[str] = None,
        title: Optional[str] = None,
        filename: Optional[str] = None
    ):
        """
        Plot metric value distribution.
        
        Args:
            metric_name: Metric name
            unit: Optional unit filter
            metadata_filters: Optional metadata filters
            chart_type: Chart type
            group_by: Optional metadata key to group by
            title: Optional chart title
            filename: Optional output filename
        """
        # Create DataFrame
        df = self.create_dataframe(
            metric_name=metric_name,
            unit=unit,
            metadata_filters=metadata_filters
        )
        
        if df.empty:
            logger.warning(f"No metrics found for {metric_name}")
            return
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Plot data
        if chart_type == ChartType.HISTOGRAM:
            if group_by and f"metadata_{group_by}" in df.columns:
                # Group by metadata key
                groups = df[f"metadata_{group_by}"].unique()
                
                for group in groups:
                    group_df = df[df[f"metadata_{group_by}"] == group]
                    plt.hist(
                        group_df["value"],
                        alpha=0.5,
                        label=str(group)
                    )
                
                plt.legend(title=group_by)
            else:
                # Plot all data
                plt.hist(df["value"])
            
            plt.xlabel(f"{metric_name} ({df['unit'].iloc[0]})")
            plt.ylabel("Frequency")
        
        elif chart_type == ChartType.BOX:
            if group_by and f"metadata_{group_by}" in df.columns:
                # Group by metadata key
                groups = []
                values = []
                
                for group in df[f"metadata_{group_by}"].unique():
                    group_df = df[df[f"metadata_{group_by}"] == group]
                    groups.append(str(group))
                    values.append(group_df["value"].tolist())
                
                plt.boxplot(values, labels=groups)
                plt.xlabel(group_by)
            else:
                # Plot all data
                plt.boxplot(df["value"])
            
            plt.ylabel(f"{metric_name} ({df['unit'].iloc[0]})")
        
        elif chart_type == ChartType.BAR:
            if group_by and f"metadata_{group_by}" in df.columns:
                # Group by metadata key
                group_stats = df.groupby(f"metadata_{group_by}")["value"].agg(
                    ["mean", "std", "min", "max"]
                )
                
                group_stats.plot(
                    kind="bar",
                    y="mean",
                    yerr="std",
                    legend=False
                )
                
                plt.xlabel(group_by)
            else:
                # Plot all data
                plt.bar(
                    ["Mean", "Median", "Min", "Max"],
                    [
                        df["value"].mean(),
                        df["value"].median(),
                        df["value"].min(),
                        df["value"].max()
                    ]
                )
            
            plt.ylabel(f"{metric_name} ({df['unit'].iloc[0]})")
        
        # Set title
        plt.title(title or f"{metric_name} distribution")
        
        # Save figure
        if filename:
            output_path = Path(self.output_dir) / filename
            plt.savefig(output_path)
            logger.info(f"Chart saved to {output_path}")
        
        # Show figure
        plt.tight_layout()
        plt.show()
    
    def plot_metric_comparison(
        self,
        metric_name: str,
        compare_by: str,
        unit: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
        chart_type: ChartType = ChartType.BAR,
        title: Optional[str] = None,
        filename: Optional[str] = None
    ):
        """
        Plot metric comparison by metadata key.
        
        Args:
            metric_name: Metric name
            compare_by: Metadata key to compare by
            unit: Optional unit filter
            metadata_filters: Optional metadata filters
            chart_type: Chart type
            title: Optional chart title
            filename: Optional output filename
        """
        # Create DataFrame
        df = self.create_dataframe(
            metric_name=metric_name,
            unit=unit,
            metadata_filters=metadata_filters
        )
        
        if df.empty:
            logger.warning(f"No metrics found for {metric_name}")
            return
        
        # Check if comparison key exists
        compare_col = f"metadata_{compare_by}"
        if compare_col not in df.columns:
            logger.warning(f"Metadata key {compare_by} not found")
            return
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Plot data
        if chart_type == ChartType.BAR:
            # Group by comparison key
            group_stats = df.groupby(compare_col)["value"].agg(
                ["mean", "std", "min", "max", "count"]
            )
            
            # Sort by mean
            group_stats = group_stats.sort_values("mean")
            
            # Plot mean with error bars
            plt.bar(
                group_stats.index,
                group_stats["mean"],
                yerr=group_stats["std"],
                capsize=5
            )
            
            # Add count labels
            for i, (idx, row) in enumerate(group_stats.iterrows()):
                plt.text(
                    i,
                    row["mean"] + row["std"] + 0.1,
                    f"n={row['count']}",
                    ha="center"
                )
            
            plt.xlabel(compare_by)
            plt.ylabel(f"{metric_name} ({df['unit'].iloc[0]})")
        
        elif chart_type == ChartType.BOX:
            # Group by comparison key
            groups = []
            values = []
            
            for group in df[compare_col].unique():
                group_df = df[df[compare_col] == group]
                groups.append(str(group))
                values.append(group_df["value"].tolist())
            
            plt.boxplot(values, labels=groups)
            plt.xlabel(compare_by)
            plt.ylabel(f"{metric_name} ({df['unit'].iloc[0]})")
        
        # Set title
        plt.title(title or f"{metric_name} comparison by {compare_by}")
        
        # Save figure
        if filename:
            output_path = Path(self.output_dir) / filename
            plt.savefig(output_path)
            logger.info(f"Chart saved to {output_path}")
        
        # Show figure
        plt.tight_layout()
        plt.show()
    
    def plot_correlation(
        self,
        metric_x: str,
        metric_y: str,
        metadata_filters: Optional[Dict[str, Any]] = None,
        group_by: Optional[str] = None,
        title: Optional[str] = None,
        filename: Optional[str] = None
    ):
        """
        Plot correlation between two metrics.
        
        Args:
            metric_x: X-axis metric name
            metric_y: Y-axis metric name
            metadata_filters: Optional metadata filters
            group_by: Optional metadata key to group by
            title: Optional chart title
            filename: Optional output filename
        """
        # Create DataFrames
        df_x = self.create_dataframe(
            metric_name=metric_x,
            metadata_filters=metadata_filters
        )
        
        df_y = self.create_dataframe(
            metric_name=metric_y,
            metadata_filters=metadata_filters
        )
        
        if df_x.empty or df_y.empty:
            logger.warning(f"No metrics found for {metric_x} or {metric_y}")
            return
        
        # Merge DataFrames
        if "metadata_request_id" in df_x.columns and "metadata_request_id" in df_y.columns:
            # Merge on request ID
            df = pd.merge(
                df_x,
                df_y,
                on="metadata_request_id",
                suffixes=("_x", "_y")
            )
        else:
            # Merge on timestamp (approximate)
            df_x["timestamp_str"] = df_x["timestamp"].astype(str)
            df_y["timestamp_str"] = df_y["timestamp"].astype(str)
            
            df = pd.merge(
                df_x,
                df_y,
                on="timestamp_str",
                suffixes=("_x", "_y")
            )
        
        if df.empty:
            logger.warning(f"No matching metrics found for {metric_x} and {metric_y}")
            return
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Plot data
        if group_by and f"metadata_{group_by}_x" in df.columns:
            # Group by metadata key
            groups = df[f"metadata_{group_by}_x"].unique()
            
            for group in groups:
                group_df = df[df[f"metadata_{group_by}_x"] == group]
                plt.scatter(
                    group_df["value_x"],
                    group_df["value_y"],
                    label=str(group),
                    alpha=0.7
                )
            
            plt.legend(title=group_by)
        else:
            # Plot all data
            plt.scatter(df["value_x"], df["value_y"], alpha=0.7)
        
        # Calculate correlation
        correlation = df["value_x"].corr(df["value_y"])
        
        # Add correlation line
        x = df["value_x"]
        y = df["value_y"]
        m, b = np.polyfit(x, y, 1)
        plt.plot(x, m*x + b, color="red", linestyle="--")
        
        # Set labels
        plt.xlabel(f"{metric_x} ({df['unit_x'].iloc[0]})")
        plt.ylabel(f"{metric_y} ({df['unit_y'].iloc[0]})")
        plt.title(title or f"Correlation between {metric_x} and {metric_y} (r={correlation:.2f})")
        
        # Save figure
        if filename:
            output_path = Path(self.output_dir) / filename
            plt.savefig(output_path)
            logger.info(f"Chart saved to {output_path}")
        
        # Show figure
        plt.tight_layout()
        plt.show()
    
    def create_dashboard(
        self,
        metrics: List[str],
        metadata_filters: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None
    ):
        """
        Create a dashboard with multiple charts.
        
        Args:
            metrics: List of metric names
            metadata_filters: Optional metadata filters
            filename: Optional output filename
        """
        # Calculate grid size
        n = len(metrics)
        cols = min(3, n)
        rows = (n + cols - 1) // cols
        
        # Create figure
        fig, axes = plt.subplots(rows, cols, figsize=(15, 5 * rows))
        
        # Flatten axes for easier indexing
        if rows == 1 and cols == 1:
            axes = np.array([axes])
        elif rows == 1 or cols == 1:
            axes = axes.flatten()
        
        # Plot each metric
        for i, metric_name in enumerate(metrics):
            if i < len(axes):
                # Get row and column
                if rows == 1 and cols == 1:
                    ax = axes[0]
                else:
                    ax = axes[i]
                
                # Create DataFrame
                df = self.create_dataframe(
                    metric_name=metric_name,
                    metadata_filters=metadata_filters
                )
                
                if not df.empty:
                    # Plot data
                    ax.plot(
                        df["timestamp"],
                        df["value"],
                        marker="o",
                        linestyle="-"
                    )
                    
                    # Set labels
                    ax.set_xlabel("Time")
                    ax.set_ylabel(f"{metric_name} ({df['unit'].iloc[0]})")
                    ax.set_title(metric_name)
                    
                    # Format x-axis
                    for label in ax.get_xticklabels():
                        label.set_rotation(45)
                        label.set_ha("right")
        
        # Hide empty subplots
        for i in range(len(metrics), len(axes)):
            fig.delaxes(axes[i])
        
        # Set title
        fig.suptitle("Performance Metrics Dashboard", fontsize=16)
        
        # Save figure
        if filename:
            output_path = Path(self.output_dir) / filename
            plt.savefig(output_path)
            logger.info(f"Dashboard saved to {output_path}")
        
        # Show figure
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.show()


# Example usage
if __name__ == "__main__":
    # Create visualizer
    visualizer = MetricsVisualizer()
    
    # Load metrics from file
    # visualizer.load_metrics_from_file("benchmark_results/response_time_benchmark_20230101_120000.json")
    
    # Plot metrics
    # visualizer.plot_metric_over_time(
    #     metric_name=MetricType.RESPONSE_TIME.value,
    #     title="Response Time Over Time",
    #     filename="response_time_over_time.png"
    # )
    
    # visualizer.plot_metric_distribution(
    #     metric_name=MetricType.RESPONSE_TIME.value,
    #     chart_type=ChartType.HISTOGRAM,
    #     title="Response Time Distribution",
    #     filename="response_time_distribution.png"
    # )
    
    # visualizer.plot_metric_comparison(
    #     metric_name=MetricType.RESPONSE_TIME.value,
    #     compare_by="model_size",
    #     chart_type=ChartType.BAR,
    #     title="Response Time by Model Size",
    #     filename="response_time_by_model_size.png"
    # )
