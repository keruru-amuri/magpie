"""
API endpoints for error tracking and monitoring.

This module provides endpoints for retrieving and managing error events.
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from pydantic import BaseModel

from app.api.deps import get_current_superuser
from app.core.monitoring import (
    ErrorSeverity,
    ErrorCategory,
    ErrorEvent,
    get_errors,
    get_error_count,
    get_error_rate,
    resolve_error,
)


router = APIRouter()


class ErrorsResponse(BaseModel):
    """
    Response model for errors endpoints.
    
    Attributes:
        errors: List of error events
        count: Number of errors returned
        total: Total number of errors matching the filters
    """
    
    errors: List[ErrorEvent]
    count: int
    total: int


class ErrorRateResponse(BaseModel):
    """
    Response model for error rate endpoint.
    
    Attributes:
        rate: Error rate (errors per minute)
        window_minutes: Time window in minutes
        count: Number of errors in the window
    """
    
    rate: float
    window_minutes: int
    count: int


@router.get("/", response_model=ErrorsResponse)
async def read_errors(
    severity: Optional[ErrorSeverity] = Query(None, description="Filter by severity level"),
    category: Optional[ErrorCategory] = Query(None, description="Filter by category"),
    component: Optional[str] = Query(None, description="Filter by component"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    start_time: Optional[datetime] = Query(None, description="Start time for filtering"),
    end_time: Optional[datetime] = Query(None, description="End time for filtering"),
    limit: int = Query(100, description="Maximum number of errors to return"),
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Get error events.
    
    This endpoint returns error events collected by the application.
    It requires superuser privileges.
    
    Args:
        severity: Filter by severity level
        category: Filter by category
        component: Filter by component
        resolved: Filter by resolution status
        start_time: Start time for filtering
        end_time: End time for filtering
        limit: Maximum number of errors to return
        current_user: Current authenticated superuser
        
    Returns:
        Dict: Dictionary with errors, count, and total
    """
    errors = get_errors(
        severity=severity,
        category=category,
        component=component,
        resolved=resolved,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    
    total = get_error_count(
        severity=severity,
        category=category,
        component=component,
        resolved=resolved,
        start_time=start_time,
        end_time=end_time,
    )
    
    return {
        "errors": errors,
        "count": len(errors),
        "total": total,
    }


@router.get("/rate", response_model=ErrorRateResponse)
async def read_error_rate(
    window_minutes: int = Query(5, description="Time window in minutes"),
    severity: Optional[ErrorSeverity] = Query(None, description="Filter by severity level"),
    category: Optional[ErrorCategory] = Query(None, description="Filter by category"),
    component: Optional[str] = Query(None, description="Filter by component"),
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Get error rate.
    
    This endpoint returns the error rate (errors per minute) for a time window.
    It requires superuser privileges.
    
    Args:
        window_minutes: Time window in minutes
        severity: Filter by severity level
        category: Filter by category
        component: Filter by component
        current_user: Current authenticated superuser
        
    Returns:
        Dict: Dictionary with error rate information
    """
    rate = get_error_rate(
        window_minutes=window_minutes,
        severity=severity,
        category=category,
        component=component,
    )
    
    # Calculate error count for the window
    start_time = datetime.now().replace(microsecond=0) - datetime.timedelta(minutes=window_minutes)
    count = get_error_count(
        severity=severity,
        category=category,
        component=component,
        start_time=start_time,
    )
    
    return {
        "rate": rate,
        "window_minutes": window_minutes,
        "count": count,
    }


@router.get("/{error_id}", response_model=ErrorEvent)
async def read_error(
    error_id: str = Path(..., description="Error ID"),
    current_user = Depends(get_current_superuser),
) -> ErrorEvent:
    """
    Get a specific error event.
    
    This endpoint returns a specific error event by ID.
    It requires superuser privileges.
    
    Args:
        error_id: Error ID
        current_user: Current authenticated superuser
        
    Returns:
        ErrorEvent: Error event
        
    Raises:
        HTTPException: If the error is not found
    """
    errors = get_errors(limit=1000)  # Get a large number of errors to search
    
    for error in errors:
        if error.id == error_id:
            return error
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Error with ID {error_id} not found",
    )


@router.post("/{error_id}/resolve", response_model=Dict)
async def resolve_error_endpoint(
    error_id: str = Path(..., description="Error ID"),
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Resolve an error.
    
    This endpoint marks an error as resolved.
    It requires superuser privileges.
    
    Args:
        error_id: Error ID
        current_user: Current authenticated superuser
        
    Returns:
        Dict: Dictionary with success status
        
    Raises:
        HTTPException: If the error is not found or could not be resolved
    """
    result = resolve_error(error_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error with ID {error_id} not found or could not be resolved",
        )
    
    return {
        "success": True,
        "message": f"Error with ID {error_id} resolved",
    }
