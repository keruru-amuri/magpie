"""
Unit tests for context pruning strategies.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.models.context import (
    ContextWindow, ContextItem, ContextType, ContextPriority
)
from app.core.context.pruning import (
    PriorityBasedPruning, RelevanceBasedPruning, TimeBasedPruning,
    HybridPruningStrategy
)
from app.core.context.monitoring import ContextWindowMonitor
from app.repositories.context import ContextItemRepository, ContextWindowRepository


class TestPruningStrategies:
    """
    Test context pruning strategies.
    """
    
    @pytest.fixture
    def mock_window(self):
        """
        Create a mock context window.
        """
        return MagicMock(spec=ContextWindow, id=1, current_tokens=100, max_tokens=80)
    
    @pytest.fixture
    def mock_items(self):
        """
        Create mock context items.
        """
        return [
            MagicMock(
                spec=ContextItem,
                id=1,
                context_window_id=1,
                context_type=ContextType.SYSTEM,
                token_count=20,
                priority=ContextPriority.CRITICAL,
                relevance_score=1.0,
                position=0,
                is_included=True
            ),
            MagicMock(
                spec=ContextItem,
                id=2,
                context_window_id=1,
                context_type=ContextType.MESSAGE,
                token_count=30,
                priority=ContextPriority.HIGH,
                relevance_score=0.9,
                position=1,
                is_included=True
            ),
            MagicMock(
                spec=ContextItem,
                id=3,
                context_window_id=1,
                context_type=ContextType.MESSAGE,
                token_count=25,
                priority=ContextPriority.MEDIUM,
                relevance_score=0.7,
                position=2,
                is_included=True
            ),
            MagicMock(
                spec=ContextItem,
                id=4,
                context_window_id=1,
                context_type=ContextType.MESSAGE,
                token_count=25,
                priority=ContextPriority.LOW,
                relevance_score=0.5,
                position=3,
                is_included=True
            )
        ]
    
    @pytest.fixture
    def mock_item_repo(self):
        """
        Create a mock context item repository.
        """
        repo = MagicMock(spec=ContextItemRepository)
        repo.update_item_inclusion.return_value = True
        return repo
    
    @pytest.fixture
    def mock_window_repo(self):
        """
        Create a mock context window repository.
        """
        repo = MagicMock(spec=ContextWindowRepository)
        repo.get_by_id.return_value = MagicMock(spec=ContextWindow)
        return repo
    
    @pytest.fixture
    def mock_monitor(self):
        """
        Create a mock context window monitor.
        """
        monitor = MagicMock(spec=ContextWindowMonitor)
        monitor.record_pruning_result.return_value = None
        return monitor
    
    def test_priority_based_pruning(self, mock_window, mock_items, mock_item_repo, mock_window_repo, mock_monitor):
        """
        Test priority-based pruning strategy.
        """
        # Create strategy
        strategy = PriorityBasedPruning()
        
        # Apply pruning
        result = strategy.prune(
            window=mock_window,
            items=mock_items,
            max_tokens=80,
            item_repo=mock_item_repo,
            window_repo=mock_window_repo,
            monitor=mock_monitor
        )
        
        # Verify result
        assert result is True
        
        # Verify item_repo.update_item_inclusion was called for low priority item
        mock_item_repo.update_item_inclusion.assert_called_with(
            item_id=4,
            is_included=False
        )
        
        # Verify monitor.record_pruning_result was called
        mock_monitor.record_pruning_result.assert_called_once()
    
    def test_relevance_based_pruning(self, mock_window, mock_items, mock_item_repo, mock_window_repo, mock_monitor):
        """
        Test relevance-based pruning strategy.
        """
        # Create strategy
        strategy = RelevanceBasedPruning(min_relevance=0.6)
        
        # Apply pruning
        result = strategy.prune(
            window=mock_window,
            items=mock_items,
            max_tokens=80,
            item_repo=mock_item_repo,
            window_repo=mock_window_repo,
            monitor=mock_monitor
        )
        
        # Verify result
        assert result is True
        
        # Verify item_repo.update_item_inclusion was called for low relevance item
        mock_item_repo.update_item_inclusion.assert_called_with(
            item_id=4,
            is_included=False
        )
        
        # Verify monitor.record_pruning_result was called
        mock_monitor.record_pruning_result.assert_called_once()
    
    def test_time_based_pruning(self, mock_window, mock_items, mock_item_repo, mock_window_repo, mock_monitor):
        """
        Test time-based pruning strategy.
        """
        # Create strategy
        strategy = TimeBasedPruning(preserve_count=2)
        
        # Apply pruning
        result = strategy.prune(
            window=mock_window,
            items=mock_items,
            max_tokens=80,
            item_repo=mock_item_repo,
            window_repo=mock_window_repo,
            monitor=mock_monitor
        )
        
        # Verify result
        assert result is True
        
        # Verify monitor.record_pruning_result was called
        mock_monitor.record_pruning_result.assert_called_once()
    
    def test_hybrid_pruning_strategy(self, mock_window, mock_items, mock_item_repo, mock_window_repo, mock_monitor):
        """
        Test hybrid pruning strategy.
        """
        # Create strategies
        priority_strategy = PriorityBasedPruning()
        relevance_strategy = RelevanceBasedPruning()
        time_strategy = TimeBasedPruning()
        
        # Create hybrid strategy
        hybrid_strategy = HybridPruningStrategy([
            priority_strategy,
            relevance_strategy,
            time_strategy
        ])
        
        # Apply pruning
        result = hybrid_strategy.prune(
            window=mock_window,
            items=mock_items,
            max_tokens=80,
            item_repo=mock_item_repo,
            window_repo=mock_window_repo,
            monitor=mock_monitor
        )
        
        # Verify result
        assert result is True
        
        # Verify monitor.record_pruning_result was called
        mock_monitor.record_pruning_result.assert_called_once()
    
    def test_no_pruning_needed(self, mock_item_repo, mock_window_repo, mock_monitor):
        """
        Test case where no pruning is needed.
        """
        # Create window with tokens under limit
        window = MagicMock(spec=ContextWindow, id=1, current_tokens=70, max_tokens=80)
        
        # Create items
        items = [
            MagicMock(
                spec=ContextItem,
                id=1,
                context_window_id=1,
                context_type=ContextType.SYSTEM,
                token_count=20,
                priority=ContextPriority.CRITICAL,
                relevance_score=1.0,
                position=0,
                is_included=True
            ),
            MagicMock(
                spec=ContextItem,
                id=2,
                context_window_id=1,
                context_type=ContextType.MESSAGE,
                token_count=50,
                priority=ContextPriority.HIGH,
                relevance_score=0.9,
                position=1,
                is_included=True
            )
        ]
        
        # Create strategy
        strategy = PriorityBasedPruning()
        
        # Apply pruning
        result = strategy.prune(
            window=window,
            items=items,
            max_tokens=80,
            item_repo=mock_item_repo,
            window_repo=mock_window_repo,
            monitor=mock_monitor
        )
        
        # Verify result
        assert result is True
        
        # Verify item_repo.update_item_inclusion was not called
        mock_item_repo.update_item_inclusion.assert_not_called()
        
        # Verify monitor.record_pruning_result was not called
        mock_monitor.record_pruning_result.assert_not_called()
    
    def test_pruning_with_no_monitor(self, mock_window, mock_items, mock_item_repo, mock_window_repo):
        """
        Test pruning without a monitor.
        """
        # Create strategy
        strategy = PriorityBasedPruning()
        
        # Apply pruning
        result = strategy.prune(
            window=mock_window,
            items=mock_items,
            max_tokens=80,
            item_repo=mock_item_repo,
            window_repo=mock_window_repo,
            monitor=None
        )
        
        # Verify result
        assert result is True
        
        # Verify item_repo.update_item_inclusion was called
        mock_item_repo.update_item_inclusion.assert_called()
