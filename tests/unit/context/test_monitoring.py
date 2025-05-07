"""
Unit tests for context window monitoring.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.models.context import (
    ContextWindow, ContextItem, ContextType, ContextPriority
)
from app.core.context.monitoring import ContextWindowMetrics, ContextWindowMonitor
from app.core.cache.connection import RedisCache


class TestContextWindowMonitoring:
    """
    Test context window monitoring.
    """
    
    @pytest.fixture
    def mock_session(self):
        """
        Create a mock session.
        """
        session = MagicMock()
        session.get.return_value = MagicMock(spec=ContextWindow)
        return session
    
    @pytest.fixture
    def mock_cache(self):
        """
        Create a mock Redis cache.
        """
        cache = MagicMock(spec=RedisCache)
        cache.lpush.return_value = None
        cache.ltrim.return_value = None
        cache.expire.return_value = None
        cache.incrby.return_value = None
        cache.incr.return_value = None
        cache.set.return_value = None
        cache.get.return_value = "10"
        cache.lrange.return_value = []
        cache.keys.return_value = []
        return cache
    
    @pytest.fixture
    def mock_window(self):
        """
        Create a mock context window.
        """
        return MagicMock(
            spec=ContextWindow,
            id=1,
            conversation_id=1,
            max_tokens=4000,
            current_tokens=2000,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def metrics(self, mock_session, mock_cache):
        """
        Create a context window metrics instance.
        """
        return ContextWindowMetrics(mock_session, mock_cache)
    
    @pytest.fixture
    def monitor(self, mock_session, mock_cache):
        """
        Create a context window monitor instance.
        """
        return ContextWindowMonitor(mock_session, mock_cache)
    
    def test_record_window_usage(self, metrics, mock_cache):
        """
        Test recording window usage.
        """
        # Record usage
        metrics.record_window_usage(window_id=1, tokens_used=100)
        
        # Verify cache operations
        mock_cache.lpush.assert_called()
        mock_cache.ltrim.assert_called()
        mock_cache.expire.assert_called()
        mock_cache.incrby.assert_called()
        mock_cache.incr.assert_called()
        mock_cache.set.assert_called()
    
    def test_record_pruning_event(self, metrics, mock_cache):
        """
        Test recording a pruning event.
        """
        # Record pruning event
        metrics.record_pruning_event(
            window_id=1,
            strategy_name="PriorityBasedPruning",
            tokens_before=2000,
            tokens_after=1500,
            items_removed=5
        )
        
        # Verify cache operations
        mock_cache.lpush.assert_called()
        mock_cache.ltrim.assert_called()
        mock_cache.expire.assert_called()
        mock_cache.incrby.assert_called()
        mock_cache.incr.assert_called()
    
    def test_get_window_metrics(self, metrics, mock_session, mock_window, mock_cache):
        """
        Test getting window metrics.
        """
        # Mock session.get to return the window
        mock_session.get.return_value = mock_window
        
        # Mock session.execute for queries
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            total_items=10,
            total_tokens=2000,
            avg_tokens_per_item=200
        )
        mock_session.execute.return_value = mock_result
        
        # Get metrics
        result = metrics.get_window_metrics(window_id=1)
        
        # Verify result
        assert result is not None
        assert "window_id" in result
        assert "conversation_id" in result
        assert "max_tokens" in result
        assert "current_tokens" in result
        assert "is_active" in result
        assert "created_at" in result
        assert "updated_at" in result
        assert "usage_history" in result
        assert "pruning_history" in result
        assert "current_stats" in result
    
    def test_get_global_metrics(self, metrics, mock_session, mock_cache):
        """
        Test getting global metrics.
        """
        # Mock session.execute for queries
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            total_windows=5,
            total_tokens=10000,
            avg_tokens_per_window=2000,
            total_items=50,
            avg_tokens_per_item=200
        )
        mock_session.execute.return_value = mock_result
        
        # Get metrics
        result = metrics.get_global_metrics()
        
        # Verify result
        assert result is not None
        assert "runtime_metrics" in result
        assert "pruning_metrics" in result
        assert "database_metrics" in result
    
    def test_get_window_health(self, metrics, mock_session, mock_window):
        """
        Test getting window health.
        """
        # Mock session.get to return the window
        mock_session.get.return_value = mock_window
        
        # Get health
        is_healthy, message, details = metrics.get_window_health(window_id=1)
        
        # Verify result
        assert is_healthy is True
        assert message is not None
        assert details is not None
        assert "window_id" in details
        assert "max_tokens" in details
        assert "current_tokens" in details
        assert "token_usage_percent" in details
    
    def test_monitor_window(self, monitor, mock_session, mock_window):
        """
        Test monitoring a window.
        """
        # Mock session.get to return the window
        mock_session.get.return_value = mock_window
        
        # Mock metrics.get_window_health
        with patch.object(ContextWindowMetrics, 'get_window_health') as mock_get_health:
            mock_get_health.return_value = (True, "Healthy", {"token_usage_percent": 50})
            
            # Mock metrics.get_window_metrics
            with patch.object(ContextWindowMetrics, 'get_window_metrics') as mock_get_metrics:
                mock_get_metrics.return_value = {"window_id": 1}
                
                # Monitor window
                result = monitor.monitor_window(window_id=1)
                
                # Verify result
                assert result is not None
                assert "window_id" in result
                assert "is_healthy" in result
                assert "message" in result
                assert "details" in result
                assert "metrics" in result
    
    def test_get_windows_requiring_pruning(self, monitor, mock_session):
        """
        Test getting windows requiring pruning.
        """
        # Mock session.execute
        mock_result = MagicMock()
        mock_result.__iter__.return_value = [(1,), (2,)]
        mock_session.execute.return_value = mock_result
        
        # Get windows requiring pruning
        result = monitor.get_windows_requiring_pruning(threshold_percent=75)
        
        # Verify result
        assert result == [1, 2]
    
    def test_record_pruning_result(self, monitor):
        """
        Test recording pruning result.
        """
        # Mock metrics.record_pruning_event
        with patch.object(ContextWindowMetrics, 'record_pruning_event') as mock_record:
            # Record pruning result
            monitor.record_pruning_result(
                window_id=1,
                strategy_name="PriorityBasedPruning",
                tokens_before=2000,
                tokens_after=1500,
                items_removed=5
            )
            
            # Verify metrics.record_pruning_event was called
            mock_record.assert_called_once_with(
                window_id=1,
                strategy_name="PriorityBasedPruning",
                tokens_before=2000,
                tokens_after=1500,
                items_removed=5
            )
    
    def test_get_global_status(self, monitor):
        """
        Test getting global status.
        """
        # Mock metrics.get_global_metrics
        with patch.object(ContextWindowMetrics, 'get_global_metrics') as mock_get_metrics:
            mock_get_metrics.return_value = {"runtime_metrics": {}}
            
            # Mock get_windows_requiring_pruning
            with patch.object(ContextWindowMonitor, 'get_windows_requiring_pruning') as mock_get_windows:
                mock_get_windows.return_value = [1, 2]
                
                # Get global status
                result = monitor.get_global_status()
                
                # Verify result
                assert result is not None
                assert "timestamp" in result
                assert "metrics" in result
                assert "windows_requiring_pruning" in result
                assert "windows_requiring_pruning_count" in result
                assert result["windows_requiring_pruning"] == [1, 2]
                assert result["windows_requiring_pruning_count"] == 2
