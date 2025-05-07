"""
API endpoints for metrics and monitoring.

This module provides endpoints for retrieving performance metrics
and monitoring information.
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.deps import get_current_superuser
from app.core.monitoring import (
    PerformanceMetric,
    get_metrics,
    get_performance_summary,
    get_slow_operations,
    PerformanceCategory
)


router = APIRouter()


class MetricsResponse(BaseModel):
    """
    Response model for metrics endpoints.

    Attributes:
        metrics: List of performance metrics
        count: Number of metrics returned
    """

    metrics: List[PerformanceMetric]
    count: int


@router.get("/", response_model=MetricsResponse)
async def read_metrics(
    name: Optional[str] = Query(None, description="Filter by metric name"),
    start_time: Optional[datetime] = Query(None, description="Start time for filtering"),
    end_time: Optional[datetime] = Query(None, description="End time for filtering"),
    limit: int = Query(100, description="Maximum number of metrics to return"),
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Get performance metrics.

    This endpoint returns performance metrics collected by the application.
    It requires superuser privileges.

    Args:
        name: Filter by metric name
        start_time: Start time for filtering
        end_time: End time for filtering
        limit: Maximum number of metrics to return
        current_user: Current authenticated superuser

    Returns:
        Dict: Dictionary with metrics and count
    """
    metrics = get_metrics(name, start_time, end_time, limit)

    return {
        "metrics": metrics,
        "count": len(metrics),
    }


@router.get("/summary", response_model=Dict)
async def read_metrics_summary(
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Get a summary of performance metrics.

    This endpoint returns a summary of performance metrics collected by the application.
    It requires superuser privileges.

    Args:
        current_user: Current authenticated superuser

    Returns:
        Dict: Dictionary with metrics summary
    """
    # Get request metrics
    request_metrics = get_metrics("http_requests_total")
    response_metrics = get_metrics("http_responses_total")
    error_metrics = get_metrics("http_errors_total")
    duration_metrics = get_metrics("http_request_duration_milliseconds")

    # Calculate total requests
    total_requests = len(request_metrics)
    total_responses = len(response_metrics)
    total_errors = len(error_metrics)

    # Calculate average duration
    avg_duration = 0
    if duration_metrics:
        avg_duration = sum(metric.value for metric in duration_metrics) / len(duration_metrics)

    # Group metrics by path
    path_metrics = {}
    for metric in response_metrics:
        path = metric.tags.get("path", "unknown")
        status = metric.tags.get("status", "unknown")

        if path not in path_metrics:
            path_metrics[path] = {"total": 0, "status_codes": {}}

        path_metrics[path]["total"] += 1

        if status not in path_metrics[path]["status_codes"]:
            path_metrics[path]["status_codes"][status] = 0

        path_metrics[path]["status_codes"][status] += 1

    return {
        "total_requests": total_requests,
        "total_responses": total_responses,
        "total_errors": total_errors,
        "average_duration_ms": avg_duration,
        "paths": path_metrics,
    }


@router.get("/performance", response_model=Dict)
async def read_performance_summary(
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Get a summary of performance profiling data.

    This endpoint returns a summary of performance profiling data collected by the application.
    It requires superuser privileges.

    Args:
        current_user: Current authenticated superuser

    Returns:
        Dict: Dictionary with performance summary
    """
    return get_performance_summary()


@router.get("/performance/slow", response_model=List[Dict])
async def read_slow_operations(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(10, description="Maximum number of operations to return"),
    current_user = Depends(get_current_superuser),
) -> List[Dict]:
    """
    Get slow operations.

    This endpoint returns a list of slow operations detected by the performance profiling system.
    It requires superuser privileges.

    Args:
        category: Filter by category (api, database, llm, cache, agent, orchestrator, etc.)
        limit: Maximum number of operations to return
        current_user: Current authenticated superuser

    Returns:
        List[Dict]: List of slow operations
    """
    return get_slow_operations(category, limit)
