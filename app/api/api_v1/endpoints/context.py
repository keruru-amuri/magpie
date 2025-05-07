"""
Context management endpoints for MAGPIE platform.
"""
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.context.monitoring import ContextWindowMonitor
from app.core.context.pruning import (
    PriorityBasedPruning, RelevanceBasedPruning, TimeBasedPruning,
    HybridPruningStrategy, default_pruning_strategy
)
from app.repositories.context import (
    ContextWindowRepository, ContextItemRepository
)

router = APIRouter()


@router.get(
    "/context/windows/{window_id}/status",
    summary="Get context window status",
    response_model=Dict[str, Any]
)
async def get_window_status(
    window_id: int = Path(..., description="Context window ID"),
    db: Session = Depends(get_db)
):
    """
    Get status of a context window.

    Args:
        window_id: Context window ID
        db: Database session

    Returns:
        Dict[str, Any]: Window status
    """
    monitor = ContextWindowMonitor(db)
    status = monitor.monitor_window(window_id)

    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])

    return status


@router.get(
    "/context/status",
    summary="Get global context status",
    response_model=Dict[str, Any]
)
async def get_global_status(
    db: Session = Depends(get_db)
):
    """
    Get global context status.

    Args:
        db: Database session

    Returns:
        Dict[str, Any]: Global status
    """
    monitor = ContextWindowMonitor(db)
    status = monitor.get_global_status()

    if "error" in status:
        raise HTTPException(status_code=500, detail=status["error"])

    return status


@router.post(
    "/context/windows/{window_id}/prune",
    summary="Prune a context window",
    response_model=Dict[str, Any]
)
async def prune_window(
    window_id: int = Path(..., description="Context window ID"),
    strategy: str = Query("hybrid", description="Pruning strategy to use"),
    max_tokens: Optional[int] = Query(None, description="Maximum tokens to keep"),
    db: Session = Depends(get_db)
):
    """
    Prune a context window.

    Args:
        window_id: Context window ID
        strategy: Pruning strategy to use
        max_tokens: Maximum tokens to keep
        db: Database session

    Returns:
        Dict[str, Any]: Pruning result
    """
    # Get repositories
    window_repo = ContextWindowRepository(db)
    item_repo = ContextItemRepository(db)
    monitor = ContextWindowMonitor(db)

    # Get window
    window = window_repo.get_by_id(window_id)
    if not window:
        raise HTTPException(status_code=404, detail=f"Window {window_id} not found")

    # Get items
    items = item_repo.get_items_for_window(window_id, included_only=True)

    # Use provided max_tokens or window's max_tokens
    target_max_tokens = max_tokens or window.max_tokens

    # Select pruning strategy
    if strategy == "priority":
        pruning_strategy = PriorityBasedPruning()
    elif strategy == "relevance":
        pruning_strategy = RelevanceBasedPruning()
    elif strategy == "time":
        pruning_strategy = TimeBasedPruning()
    elif strategy == "hybrid":
        pruning_strategy = default_pruning_strategy
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pruning strategy: {strategy}. "
                  f"Valid options are: priority, relevance, time, hybrid"
        )

    # Record initial state
    tokens_before = window.current_tokens
    items_before = len(items)

    # Apply pruning
    success = pruning_strategy.prune(
        window=window,
        items=items,
        max_tokens=target_max_tokens,
        item_repo=item_repo,
        window_repo=window_repo,
        monitor=monitor
    )

    if not success:
        raise HTTPException(status_code=500, detail="Pruning failed")

    # Get updated window
    window = window_repo.get_by_id(window_id)
    items_after = len(item_repo.get_items_for_window(window_id, included_only=True))

    # Return result
    return {
        "window_id": window_id,
        "strategy": strategy,
        "tokens_before": tokens_before,
        "tokens_after": window.current_tokens,
        "tokens_removed": tokens_before - window.current_tokens,
        "items_before": items_before,
        "items_after": items_after,
        "items_removed": items_before - items_after,
        "success": success
    }


@router.post(
    "/context/prune-all",
    summary="Prune all context windows",
    response_model=Dict[str, Any]
)
async def prune_all_windows(
    threshold_percent: float = Query(75.0, description="Token usage threshold percentage"),
    strategy: str = Query("hybrid", description="Pruning strategy to use"),
    db: Session = Depends(get_db)
):
    """
    Prune all context windows that exceed the threshold.

    Args:
        threshold_percent: Token usage threshold percentage
        strategy: Pruning strategy to use
        db: Database session

    Returns:
        Dict[str, Any]: Pruning result
    """
    # Get repositories
    window_repo = ContextWindowRepository(db)
    item_repo = ContextItemRepository(db)
    monitor = ContextWindowMonitor(db)

    # Get windows requiring pruning
    windows_requiring_pruning = monitor.get_windows_requiring_pruning(threshold_percent)

    if not windows_requiring_pruning:
        return {
            "message": "No windows require pruning",
            "windows_pruned": 0,
            "total_tokens_removed": 0,
            "total_items_removed": 0
        }

    # Select pruning strategy
    if strategy == "priority":
        pruning_strategy = PriorityBasedPruning()
    elif strategy == "relevance":
        pruning_strategy = RelevanceBasedPruning()
    elif strategy == "time":
        pruning_strategy = TimeBasedPruning()
    elif strategy == "hybrid":
        pruning_strategy = default_pruning_strategy
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pruning strategy: {strategy}. "
                  f"Valid options are: priority, relevance, time, hybrid"
        )

    # Prune each window
    windows_pruned = 0
    total_tokens_removed = 0
    total_items_removed = 0

    for window_id in windows_requiring_pruning:
        # Get window
        window = window_repo.get_by_id(window_id)
        if not window:
            continue

        # Get items
        items = item_repo.get_items_for_window(window_id, included_only=True)
        items_before = len(items)
        tokens_before = window.current_tokens

        # Apply pruning
        success = pruning_strategy.prune(
            window=window,
            items=items,
            max_tokens=window.max_tokens,
            item_repo=item_repo,
            window_repo=window_repo,
            monitor=monitor
        )

        if success:
            # Get updated window
            window = window_repo.get_by_id(window_id)
            items_after = len(item_repo.get_items_for_window(window_id, included_only=True))

            # Update counters
            windows_pruned += 1
            total_tokens_removed += tokens_before - window.current_tokens
            total_items_removed += items_before - items_after

    # Return result
    return {
        "message": f"Pruned {windows_pruned} windows",
        "windows_pruned": windows_pruned,
        "total_tokens_removed": total_tokens_removed,
        "total_items_removed": total_items_removed,
        "windows_requiring_pruning": len(windows_requiring_pruning)
    }
