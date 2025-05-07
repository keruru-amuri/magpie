"""
API endpoints for database operations and monitoring.

This module provides endpoints for retrieving database performance metrics
and optimization recommendations.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_superuser, get_db
from app.core.db.optimizer import query_optimizer
from app.core.cache.query_cache import query_cache_manager


router = APIRouter()


@router.get("/performance", response_model=Dict)
async def read_database_performance(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Get database performance metrics.
    
    This endpoint returns database performance metrics and optimization recommendations.
    It requires superuser privileges.
    
    Args:
        db: Database session
        current_user: Current authenticated superuser
        
    Returns:
        Dict: Dictionary with database performance metrics
    """
    # Get optimization recommendations
    recommendations = query_optimizer.get_optimization_recommendations(db)
    
    return recommendations


@router.get("/slow-queries", response_model=List[Dict])
async def read_slow_queries(
    limit: int = Query(10, description="Maximum number of queries to return"),
    current_user = Depends(get_current_superuser),
) -> List[Dict]:
    """
    Get slow queries.
    
    This endpoint returns a list of slow queries detected by the query optimizer.
    It requires superuser privileges.
    
    Args:
        limit: Maximum number of queries to return
        current_user: Current authenticated superuser
        
    Returns:
        List[Dict]: List of slow queries
    """
    # Get slow queries
    slow_queries = query_optimizer.get_slow_queries(limit)
    
    return slow_queries


@router.post("/clear-slow-queries", response_model=Dict)
async def clear_slow_queries(
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Clear slow queries.
    
    This endpoint clears the list of slow queries detected by the query optimizer.
    It requires superuser privileges.
    
    Args:
        current_user: Current authenticated superuser
        
    Returns:
        Dict: Success message
    """
    # Clear slow queries
    query_optimizer.clear_slow_queries()
    
    return {"message": "Slow queries cleared"}


@router.post("/clear-query-cache", response_model=Dict)
async def clear_query_cache(
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Clear query cache.
    
    This endpoint clears the query cache.
    It requires superuser privileges.
    
    Args:
        current_user: Current authenticated superuser
        
    Returns:
        Dict: Success message with number of keys deleted
    """
    # Clear query cache
    deleted_count = query_cache_manager.clear_all_query_cache()
    
    return {
        "message": "Query cache cleared",
        "deleted_count": deleted_count,
    }


@router.get("/table-statistics", response_model=Dict)
async def read_table_statistics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Get table statistics.
    
    This endpoint returns statistics for tables in the database.
    It requires superuser privileges.
    
    Args:
        db: Database session
        current_user: Current authenticated superuser
        
    Returns:
        Dict: Dictionary with table statistics
    """
    # Get table statistics
    table_stats = query_optimizer.get_table_statistics(db)
    
    return {"table_statistics": table_stats}


@router.get("/index-usage", response_model=Dict)
async def read_index_usage(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Get index usage statistics.
    
    This endpoint returns index usage statistics for the database.
    It requires superuser privileges.
    
    Args:
        db: Database session
        current_user: Current authenticated superuser
        
    Returns:
        Dict: Dictionary with index usage statistics
    """
    # Get index usage
    index_usage = query_optimizer.get_index_usage(db)
    
    return {"index_usage": index_usage}


@router.get("/missing-indexes", response_model=Dict)
async def read_missing_indexes(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_superuser),
) -> Dict:
    """
    Get missing indexes.
    
    This endpoint returns a list of tables and columns that might benefit from indexes.
    It requires superuser privileges.
    
    Args:
        db: Database session
        current_user: Current authenticated superuser
        
    Returns:
        Dict: Dictionary with missing indexes
    """
    # Get missing indexes
    missing_indexes = query_optimizer.check_missing_indexes(db)
    
    return {"missing_indexes": missing_indexes}
