"""
Unit tests for database query optimizer.
"""

import pytest
from unittest.mock import MagicMock, patch

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.db.optimizer import QueryOptimizer, optimized_query


class TestQueryOptimizer:
    """
    Test query optimizer functionality.
    """
    
    def test_initialization(self):
        """
        Test query optimizer initialization.
        """
        # Initialize optimizer
        optimizer = QueryOptimizer(enabled=True)
        
        # Verify initialization
        assert optimizer.enabled is True
        assert optimizer.slow_query_threshold_ms == 100
        assert isinstance(optimizer.tables_missing_indexes, set)
        assert isinstance(optimizer.slow_queries, dict)
    
    def test_analyze_query_string(self):
        """
        Test analyze_query method with string query.
        """
        # Initialize optimizer
        optimizer = QueryOptimizer(enabled=True)
        
        # Analyze query
        query = "SELECT * FROM users WHERE id = 1"
        duration_ms = 50.0
        
        analysis = optimizer.analyze_query(query, duration_ms)
        
        # Verify analysis
        assert analysis["query"] == query
        assert analysis["duration_ms"] == duration_ms
        assert analysis["is_slow"] is False
        assert analysis["tables"] == []
        assert "timestamp" in analysis
    
    def test_analyze_slow_query(self):
        """
        Test analyze_query method with slow query.
        """
        # Initialize optimizer
        optimizer = QueryOptimizer(enabled=True, slow_query_threshold_ms=10)
        
        # Analyze query
        query = "SELECT * FROM users WHERE id = 1"
        duration_ms = 50.0
        
        analysis = optimizer.analyze_query(query, duration_ms)
        
        # Verify analysis
        assert analysis["query"] == query
        assert analysis["duration_ms"] == duration_ms
        assert analysis["is_slow"] is True
        assert analysis["tables"] == []
        assert "timestamp" in analysis
        
        # Verify slow query was added
        assert len(optimizer.slow_queries) == 1
    
    def test_get_slow_queries(self):
        """
        Test get_slow_queries method.
        """
        # Initialize optimizer
        optimizer = QueryOptimizer(enabled=True, slow_query_threshold_ms=10)
        
        # Add slow queries
        query1 = "SELECT * FROM users WHERE id = 1"
        query2 = "SELECT * FROM posts WHERE user_id = 1"
        
        optimizer.analyze_query(query1, 50.0)
        optimizer.analyze_query(query2, 100.0)
        
        # Get slow queries
        slow_queries = optimizer.get_slow_queries()
        
        # Verify slow queries
        assert len(slow_queries) == 2
        assert slow_queries[0]["duration_ms"] > slow_queries[1]["duration_ms"]
    
    def test_clear_slow_queries(self):
        """
        Test clear_slow_queries method.
        """
        # Initialize optimizer
        optimizer = QueryOptimizer(enabled=True, slow_query_threshold_ms=10)
        
        # Add slow queries
        query = "SELECT * FROM users WHERE id = 1"
        optimizer.analyze_query(query, 50.0)
        
        # Verify slow query was added
        assert len(optimizer.slow_queries) == 1
        
        # Clear slow queries
        optimizer.clear_slow_queries()
        
        # Verify slow queries were cleared
        assert len(optimizer.slow_queries) == 0
    
    def test_check_missing_indexes_not_postgresql(self):
        """
        Test check_missing_indexes method with non-PostgreSQL database.
        """
        # Initialize optimizer
        optimizer = QueryOptimizer(enabled=True)
        
        # Mock session
        session = MagicMock(spec=Session)
        
        # Check missing indexes
        with patch("app.core.db.optimizer.settings") as mock_settings:
            mock_settings.DATABASE_URL = "sqlite:///test.db"
            missing_indexes = optimizer.check_missing_indexes(session)
        
        # Verify missing indexes
        assert missing_indexes == {}
    
    def test_get_table_statistics_not_postgresql(self):
        """
        Test get_table_statistics method with non-PostgreSQL database.
        """
        # Initialize optimizer
        optimizer = QueryOptimizer(enabled=True)
        
        # Mock session
        session = MagicMock(spec=Session)
        
        # Get table statistics
        with patch("app.core.db.optimizer.settings") as mock_settings:
            mock_settings.DATABASE_URL = "sqlite:///test.db"
            table_stats = optimizer.get_table_statistics(session)
        
        # Verify table statistics
        assert table_stats == {}
    
    def test_get_index_usage_not_postgresql(self):
        """
        Test get_index_usage method with non-PostgreSQL database.
        """
        # Initialize optimizer
        optimizer = QueryOptimizer(enabled=True)
        
        # Mock session
        session = MagicMock(spec=Session)
        
        # Get index usage
        with patch("app.core.db.optimizer.settings") as mock_settings:
            mock_settings.DATABASE_URL = "sqlite:///test.db"
            index_usage = optimizer.get_index_usage(session)
        
        # Verify index usage
        assert index_usage == {}
    
    def test_get_optimization_recommendations(self):
        """
        Test get_optimization_recommendations method.
        """
        # Initialize optimizer
        optimizer = QueryOptimizer(enabled=True)
        
        # Mock methods
        optimizer.check_missing_indexes = MagicMock(return_value={"users": ["id", "email"]})
        optimizer.get_table_statistics = MagicMock(return_value={"users": {"row_count": 100}})
        optimizer.get_index_usage = MagicMock(return_value={"users": {"users_pkey": {"index_scans": 100}}})
        optimizer.get_slow_queries = MagicMock(return_value=[{"query": "SELECT * FROM users", "duration_ms": 50.0}])
        
        # Mock session
        session = MagicMock(spec=Session)
        
        # Get optimization recommendations
        recommendations = optimizer.get_optimization_recommendations(session)
        
        # Verify recommendations
        assert recommendations["enabled"] is True
        assert recommendations["missing_indexes"] == {"users": ["id", "email"]}
        assert recommendations["table_stats"] == {"users": {"row_count": 100}}
        assert recommendations["index_usage"] == {"users": {"users_pkey": {"index_scans": 100}}}
        assert recommendations["slow_queries"] == [{"query": "SELECT * FROM users", "duration_ms": 50.0}]
        assert "timestamp" in recommendations
    
    def test_optimized_query_decorator(self):
        """
        Test optimized_query decorator.
        """
        # Mock query optimizer
        with patch("app.core.db.optimizer.query_optimizer") as mock_optimizer:
            mock_optimizer.enabled = True
            mock_optimizer.analyze_query = MagicMock()
            
            # Define decorated function
            @optimized_query
            def test_function():
                query = select(1)
                return query
            
            # Call decorated function
            result = test_function()
            
            # Verify result
            assert result is not None
            
            # Verify optimizer was not called (since result is not a Query object)
            mock_optimizer.analyze_query.assert_not_called()
    
    def test_optimized_query_decorator_with_query(self):
        """
        Test optimized_query decorator with Query object.
        """
        # Mock query optimizer
        with patch("app.core.db.optimizer.query_optimizer") as mock_optimizer, \
             patch("app.core.db.optimizer.time") as mock_time:
            mock_optimizer.enabled = True
            mock_optimizer.analyze_query = MagicMock()
            mock_time.time.side_effect = [0, 0.1]  # Start time, end time
            
            # Define decorated function
            @optimized_query
            def test_function():
                query = MagicMock()
                query.statement = "SELECT 1"
                return query
            
            # Call decorated function
            result = test_function()
            
            # Verify result
            assert result is not None
            
            # Verify optimizer was called
            mock_optimizer.analyze_query.assert_called_once()
            args, kwargs = mock_optimizer.analyze_query.call_args
            assert args[0] == result
            assert args[1] == 100.0  # 0.1 seconds = 100 ms
