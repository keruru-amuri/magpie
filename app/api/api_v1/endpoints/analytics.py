"""
API endpoints for usage analytics and cost tracking.

This module provides endpoints for retrieving usage analytics and cost metrics.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, Query, Path
from pydantic import BaseModel

from app.api.deps import get_current_superuser
from app.core.monitoring import (
    ModelSize,
    UsageRecord,
    AnalyticsPeriod,
    get_user_metrics,
    get_model_metrics,
    get_agent_metrics,
    get_global_metrics,
    get_usage_records,
)


router = APIRouter()


class UsageRecordResponse(BaseModel):
    """
    Response model for usage records.
    
    Attributes:
        records: List of usage records
        count: Number of records returned
    """
    
    records: List[UsageRecord]
    count: int


@router.get("/usage", response_model=UsageRecordResponse)
async def read_usage_records(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    model_size: Optional[ModelSize] = Query(None, description="Filter by model size"),
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    limit: int = Query(100, description="Maximum number of records to return"),
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Get usage records.
    
    This endpoint returns usage records for API calls.
    It requires superuser privileges.
    
    Args:
        user_id: Filter by user ID
        model_size: Filter by model size
        agent_type: Filter by agent type
        start_date: Start date for filtering
        end_date: End date for filtering
        limit: Maximum number of records to return
        current_user: Current authenticated superuser
        
    Returns:
        Dict: Dictionary with usage records and count
    """
    records = get_usage_records(
        user_id=user_id,
        model_size=model_size,
        agent_type=agent_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    
    return {
        "records": records,
        "count": len(records),
    }


@router.get("/user/{user_id}")
async def read_user_metrics(
    user_id: str = Path(..., description="User ID"),
    period: AnalyticsPeriod = Query(AnalyticsPeriod.DAILY, description="Analytics period"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Get metrics for a specific user.
    
    This endpoint returns usage metrics for a specific user.
    It requires superuser privileges.
    
    Args:
        user_id: User ID
        period: Analytics period
        start_date: Start date for filtering
        end_date: End date for filtering
        current_user: Current authenticated superuser
        
    Returns:
        Dict: Dictionary with user metrics
    """
    return get_user_metrics(
        user_id=user_id,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/model/{model_size}")
async def read_model_metrics(
    model_size: ModelSize = Path(..., description="Model size"),
    period: AnalyticsPeriod = Query(AnalyticsPeriod.DAILY, description="Analytics period"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Get metrics for a specific model.
    
    This endpoint returns usage metrics for a specific model.
    It requires superuser privileges.
    
    Args:
        model_size: Model size
        period: Analytics period
        start_date: Start date for filtering
        end_date: End date for filtering
        current_user: Current authenticated superuser
        
    Returns:
        Dict: Dictionary with model metrics
    """
    return get_model_metrics(
        model_size=model_size,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/agent/{agent_type}")
async def read_agent_metrics(
    agent_type: str = Path(..., description="Agent type"),
    period: AnalyticsPeriod = Query(AnalyticsPeriod.DAILY, description="Analytics period"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Get metrics for a specific agent.
    
    This endpoint returns usage metrics for a specific agent.
    It requires superuser privileges.
    
    Args:
        agent_type: Agent type
        period: Analytics period
        start_date: Start date for filtering
        end_date: End date for filtering
        current_user: Current authenticated superuser
        
    Returns:
        Dict: Dictionary with agent metrics
    """
    return get_agent_metrics(
        agent_type=agent_type,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/global")
async def read_global_metrics(
    period: AnalyticsPeriod = Query(AnalyticsPeriod.DAILY, description="Analytics period"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Get global metrics.
    
    This endpoint returns global usage metrics.
    It requires superuser privileges.
    
    Args:
        period: Analytics period
        start_date: Start date for filtering
        end_date: End date for filtering
        current_user: Current authenticated superuser
        
    Returns:
        Dict: Dictionary with global metrics
    """
    return get_global_metrics(
        period=period,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/summary")
async def read_analytics_summary(
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Get analytics summary.
    
    This endpoint returns a summary of usage analytics.
    It requires superuser privileges.
    
    Args:
        current_user: Current authenticated superuser
        
    Returns:
        Dict: Dictionary with analytics summary
    """
    # Get global metrics for different periods
    daily = get_global_metrics(period=AnalyticsPeriod.DAILY)
    weekly = get_global_metrics(period=AnalyticsPeriod.WEEKLY)
    monthly = get_global_metrics(period=AnalyticsPeriod.MONTHLY)
    all_time = get_global_metrics(period=AnalyticsPeriod.ALL_TIME)
    
    # Get metrics for each model size
    small_model = get_model_metrics(model_size=ModelSize.SMALL, period=AnalyticsPeriod.ALL_TIME)
    medium_model = get_model_metrics(model_size=ModelSize.MEDIUM, period=AnalyticsPeriod.ALL_TIME)
    large_model = get_model_metrics(model_size=ModelSize.LARGE, period=AnalyticsPeriod.ALL_TIME)
    
    # Create summary
    return {
        "daily": daily.get("total", {}),
        "weekly": weekly.get("total", {}),
        "monthly": monthly.get("total", {}),
        "all_time": all_time.get("metrics", {}),
        "models": {
            "small": small_model.get("metrics", {}),
            "medium": medium_model.get("metrics", {}),
            "large": large_model.get("metrics", {}),
        },
    }
