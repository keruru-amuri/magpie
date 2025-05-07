"""
Context pruning strategies for the MAGPIE platform.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any, Tuple

from app.models.context import (
    ContextWindow, ContextItem, ContextType, ContextPriority
)
from app.repositories.context import ContextItemRepository, ContextWindowRepository
from app.core.context.monitoring import ContextWindowMonitor

# Configure logging
logger = logging.getLogger(__name__)


class PruningStrategy(ABC):
    """
    Abstract base class for context pruning strategies.
    """

    @property
    def name(self) -> str:
        """
        Get the name of the pruning strategy.

        Returns:
            str: Strategy name
        """
        return self.__class__.__name__

    @abstractmethod
    def prune(
        self,
        window: ContextWindow,
        items: List[ContextItem],
        max_tokens: int,
        item_repo: ContextItemRepository,
        window_repo: ContextWindowRepository,
        monitor: Optional[ContextWindowMonitor] = None
    ) -> bool:
        """
        Prune context items to fit within token limit.

        Args:
            window: Context window
            items: Context items
            max_tokens: Maximum number of tokens
            item_repo: Context item repository
            window_repo: Context window repository
            monitor: Context window monitor for metrics collection

        Returns:
            bool: True if successful, False otherwise
        """
        pass


class PriorityBasedPruning(PruningStrategy):
    """
    Priority-based pruning strategy.

    Prunes items based on priority, preserving high-priority items.
    """

    def __init__(
        self,
        preserve_types: Optional[List[ContextType]] = None,
        preserve_priorities: Optional[List[ContextPriority]] = None
    ):
        """
        Initialize priority-based pruning strategy.

        Args:
            preserve_types: Context types to preserve
            preserve_priorities: Priority levels to preserve
        """
        self.preserve_types = preserve_types or [
            ContextType.SYSTEM,
            ContextType.USER_PREFERENCE
        ]
        self.preserve_priorities = preserve_priorities or [
            ContextPriority.CRITICAL,
            ContextPriority.HIGH
        ]

    def prune(
        self,
        window: ContextWindow,
        items: List[ContextItem],
        max_tokens: int,
        item_repo: ContextItemRepository,
        window_repo: ContextWindowRepository,
        monitor: Optional[ContextWindowMonitor] = None
    ) -> bool:
        """
        Prune context items to fit within token limit.

        Args:
            window: Context window
            items: Context items
            max_tokens: Maximum number of tokens
            item_repo: Context item repository
            window_repo: Context window repository
            monitor: Context window monitor for metrics collection

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if pruning is needed
            if window.current_tokens <= max_tokens:
                return True

            # Record initial state for monitoring
            tokens_before = window.current_tokens
            items_before = len([item for item in items if item.is_included])

            # Sort items by pruning priority (items to prune first come first)
            items.sort(
                key=lambda x: (
                    # Preserve specified types
                    0 if x.context_type in self.preserve_types else 1,
                    # Preserve specified priorities
                    0 if x.priority in self.preserve_priorities else 1,
                    # Prefer higher priorities
                    {
                        ContextPriority.CRITICAL: 0,
                        ContextPriority.HIGH: 1,
                        ContextPriority.MEDIUM: 2,
                        ContextPriority.LOW: 3
                    }.get(x.priority, 4),
                    # Prefer newer items (higher position)
                    -x.position
                )
            )

            # Calculate tokens to remove
            tokens_to_remove = window.current_tokens - max_tokens
            items_removed = 0

            # Prune items
            for item in items:
                # Skip items with preserved types and priorities
                if (item.context_type in self.preserve_types and
                        item.priority in self.preserve_priorities):
                    continue

                # Skip items that are already excluded
                if not item.is_included:
                    continue

                # Exclude item from context
                item_repo.update_item_inclusion(
                    item_id=item.id,
                    is_included=False
                )

                # Update counters
                tokens_to_remove -= item.token_count
                items_removed += 1

                # Check if we've removed enough tokens
                if tokens_to_remove <= 0:
                    break

            # Record pruning metrics if monitor is provided
            if monitor and items_removed > 0:
                monitor.record_pruning_result(
                    window_id=window.id,
                    strategy_name=self.name,
                    tokens_before=tokens_before,
                    tokens_after=window.current_tokens,
                    items_removed=items_removed
                )

            return True
        except Exception as e:
            logger.error(f"Error in priority-based pruning: {str(e)}")
            return False


class RelevanceBasedPruning(PruningStrategy):
    """
    Relevance-based pruning strategy.

    Prunes items based on relevance score, preserving most relevant items.
    """

    def __init__(
        self,
        preserve_types: Optional[List[ContextType]] = None,
        min_relevance: float = 0.5
    ):
        """
        Initialize relevance-based pruning strategy.

        Args:
            preserve_types: Context types to preserve
            min_relevance: Minimum relevance score to preserve
        """
        self.preserve_types = preserve_types or [ContextType.SYSTEM]
        self.min_relevance = min_relevance

    def prune(
        self,
        window: ContextWindow,
        items: List[ContextItem],
        max_tokens: int,
        item_repo: ContextItemRepository,
        window_repo: ContextWindowRepository,
        monitor: Optional[ContextWindowMonitor] = None
    ) -> bool:
        """
        Prune context items to fit within token limit.

        Args:
            window: Context window
            items: Context items
            max_tokens: Maximum number of tokens
            item_repo: Context item repository
            window_repo: Context window repository
            monitor: Context window monitor for metrics collection

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if pruning is needed
            if window.current_tokens <= max_tokens:
                return True

            # Record initial state for monitoring
            tokens_before = window.current_tokens
            items_removed = 0

            # Sort items by pruning priority (items to prune first come first)
            items.sort(
                key=lambda x: (
                    # Preserve specified types
                    0 if x.context_type in self.preserve_types else 1,
                    # Preserve items with high relevance
                    0 if x.relevance_score >= self.min_relevance else 1,
                    # Sort by relevance score (lower first)
                    x.relevance_score,
                    # Prefer newer items (higher position)
                    -x.position
                )
            )

            # Calculate tokens to remove
            tokens_to_remove = window.current_tokens - max_tokens

            # Prune items
            for item in items:
                # Skip preserved types
                if item.context_type in self.preserve_types:
                    continue

                # Skip items that are already excluded
                if not item.is_included:
                    continue

                # Exclude item from context
                item_repo.update_item_inclusion(
                    item_id=item.id,
                    is_included=False
                )

                # Update counters
                tokens_to_remove -= item.token_count
                items_removed += 1

                # Check if we've removed enough tokens
                if tokens_to_remove <= 0:
                    break

            # Record pruning metrics if monitor is provided
            if monitor and items_removed > 0:
                monitor.record_pruning_result(
                    window_id=window.id,
                    strategy_name=self.name,
                    tokens_before=tokens_before,
                    tokens_after=window.current_tokens,
                    items_removed=items_removed
                )

            return True
        except Exception as e:
            logger.error(f"Error in relevance-based pruning: {str(e)}")
            return False


class TimeBasedPruning(PruningStrategy):
    """
    Time-based pruning strategy.

    Prunes older items first, preserving recent context.
    """

    def __init__(
        self,
        preserve_types: Optional[List[ContextType]] = None,
        preserve_count: int = 5
    ):
        """
        Initialize time-based pruning strategy.

        Args:
            preserve_types: Context types to preserve
            preserve_count: Number of most recent items to preserve
        """
        self.preserve_types = preserve_types or [ContextType.SYSTEM]
        self.preserve_count = preserve_count

    def prune(
        self,
        window: ContextWindow,
        items: List[ContextItem],
        max_tokens: int,
        item_repo: ContextItemRepository,
        window_repo: ContextWindowRepository,
        monitor: Optional[ContextWindowMonitor] = None
    ) -> bool:
        """
        Prune context items to fit within token limit.

        Args:
            window: Context window
            items: Context items
            max_tokens: Maximum number of tokens
            item_repo: Context item repository
            window_repo: Context window repository
            monitor: Context window monitor for metrics collection

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if pruning is needed
            if window.current_tokens <= max_tokens:
                return True

            # Record initial state for monitoring
            tokens_before = window.current_tokens
            items_before = len([item for item in items if item.is_included])

            # Sort items by position (higher position = more recent)
            items.sort(key=lambda x: x.position)

            # Identify items to preserve
            preserved_items = []
            prunable_items = []

            for item in items:
                if not item.is_included:
                    continue

                if item.context_type in self.preserve_types:
                    preserved_items.append(item)
                else:
                    prunable_items.append(item)

            # Preserve the most recent items
            if len(prunable_items) > self.preserve_count:
                preserved_items.extend(prunable_items[-self.preserve_count:])
                prunable_items = prunable_items[:-self.preserve_count]
            else:
                preserved_items.extend(prunable_items)
                prunable_items = []

            # Calculate tokens in preserved items
            preserved_tokens = sum(item.token_count for item in preserved_items)

            # If preserved items already exceed max tokens, we need to prune them too
            if preserved_tokens > max_tokens:
                # Sort preserved items by priority (excluding preserve_types)
                preserved_items.sort(
                    key=lambda x: (
                        # Keep preserve_types at the end
                        0 if x.context_type in self.preserve_types else 1,
                        # Sort by position (lower first)
                        x.position
                    )
                )

                # Prune preserved items until we're under the limit
                tokens_to_remove = preserved_tokens - max_tokens
                for item in preserved_items:
                    # Skip preserve_types
                    if item.context_type in self.preserve_types:
                        continue

                    # Exclude item from context
                    item_repo.update_item_inclusion(
                        item_id=item.id,
                        is_included=False
                    )

                    # Update tokens to remove
                    tokens_to_remove -= item.token_count

                    # Move item to prunable_items
                    prunable_items.append(item)
                    preserved_items.remove(item)

                    # Check if we've removed enough tokens
                    if tokens_to_remove <= 0:
                        break
            else:
                # We have room for some prunable items
                available_tokens = max_tokens - preserved_tokens

                # Sort prunable items by recency (higher position = more recent)
                prunable_items.sort(key=lambda x: -x.position)

                # Add as many prunable items as possible
                for item in prunable_items[:]:  # Create a copy to iterate over
                    if item.token_count <= available_tokens:
                        # Keep this item
                        preserved_items.append(item)
                        available_tokens -= item.token_count
                        prunable_items.remove(item)
                    else:
                        # Can't fit this item
                        break

            # Exclude all remaining prunable items
            items_removed = 0
            for item in prunable_items:
                if item.is_included:  # Only count items that were actually included
                    item_repo.update_item_inclusion(
                        item_id=item.id,
                        is_included=False
                    )
                    items_removed += 1

            # Record pruning metrics if monitor is provided
            if monitor and items_removed > 0:
                monitor.record_pruning_result(
                    window_id=window.id,
                    strategy_name=self.name,
                    tokens_before=tokens_before,
                    tokens_after=window.current_tokens,
                    items_removed=items_removed
                )

            return True
        except Exception as e:
            logger.error(f"Error in time-based pruning: {str(e)}")
            return False


class HybridPruningStrategy(PruningStrategy):
    """
    Hybrid pruning strategy.

    Combines multiple pruning strategies.
    """

    def __init__(self, strategies: List[PruningStrategy]):
        """
        Initialize hybrid pruning strategy.

        Args:
            strategies: List of pruning strategies to apply in order
        """
        self.strategies = strategies

    def prune(
        self,
        window: ContextWindow,
        items: List[ContextItem],
        max_tokens: int,
        item_repo: ContextItemRepository,
        window_repo: ContextWindowRepository,
        monitor: Optional[ContextWindowMonitor] = None
    ) -> bool:
        """
        Prune context items to fit within token limit.

        Args:
            window: Context window
            items: Context items
            max_tokens: Maximum number of tokens
            item_repo: Context item repository
            window_repo: Context window repository
            monitor: Context window monitor for metrics collection

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if pruning is needed
            if window.current_tokens <= max_tokens:
                return True

            # Record initial state for monitoring
            tokens_before = window.current_tokens

            # Track which strategies were used
            strategies_used = []
            total_items_removed = 0

            # Apply each strategy in order
            for strategy in self.strategies:
                # Get current items (only included ones)
                current_items = [item for item in items if item.is_included]

                # Skip if we're already under the limit
                if window.current_tokens <= max_tokens:
                    break

                # Record tokens before this strategy
                strategy_tokens_before = window.current_tokens

                # Apply strategy
                success = strategy.prune(
                    window=window,
                    items=current_items,
                    max_tokens=max_tokens,
                    item_repo=item_repo,
                    window_repo=window_repo,
                    # Don't pass monitor to avoid duplicate recording
                    monitor=None
                )

                if not success:
                    logger.warning(f"Strategy {strategy.name} failed")
                    continue

                # Calculate items removed by this strategy
                strategy_items_removed = len([
                    item for item in current_items
                    if not item.is_included
                ])

                # Record strategy usage if it removed any items
                if strategy_items_removed > 0:
                    strategies_used.append(strategy.name)
                    total_items_removed += strategy_items_removed

                # Check if we're under the limit
                if window.current_tokens <= max_tokens:
                    break

            # If we're still over the limit, apply a final aggressive pruning
            if window.current_tokens > max_tokens:
                # Record tokens before final pruning
                final_tokens_before = window.current_tokens

                # Get current items
                current_items = [item for item in items if item.is_included]
                current_items.sort(key=lambda x: (
                    # Preserve system items
                    0 if x.context_type == ContextType.SYSTEM else 1,
                    # Sort by position (lower first)
                    x.position
                ))

                # Calculate tokens to remove
                tokens_to_remove = window.current_tokens - max_tokens
                final_items_removed = 0

                # Prune items
                for item in current_items:
                    # Skip system items
                    if item.context_type == ContextType.SYSTEM:
                        continue

                    # Exclude item from context
                    item_repo.update_item_inclusion(
                        item_id=item.id,
                        is_included=False
                    )

                    # Update counters
                    tokens_to_remove -= item.token_count
                    final_items_removed += 1
                    total_items_removed += 1

                    # Check if we've removed enough tokens
                    if tokens_to_remove <= 0:
                        break

                # Record final strategy usage if it removed any items
                if final_items_removed > 0:
                    strategies_used.append("AggressiveFallback")

            # Record pruning metrics if monitor is provided
            if monitor and total_items_removed > 0:
                strategy_name = "Hybrid(" + "+".join(strategies_used) + ")"
                monitor.record_pruning_result(
                    window_id=window.id,
                    strategy_name=strategy_name,
                    tokens_before=tokens_before,
                    tokens_after=window.current_tokens,
                    items_removed=total_items_removed
                )

            return True
        except Exception as e:
            logger.error(f"Error in hybrid pruning: {str(e)}")
            return False


# Create default pruning strategies
default_priority_pruning = PriorityBasedPruning()
default_relevance_pruning = RelevanceBasedPruning()
default_time_pruning = TimeBasedPruning()

# Create default hybrid strategy
default_pruning_strategy = HybridPruningStrategy([
    default_priority_pruning,
    default_relevance_pruning,
    default_time_pruning
])
