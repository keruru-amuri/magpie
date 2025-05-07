"""
Unit tests for query cache manager.
"""

import pytest
import time
from unittest.mock import MagicMock, patch

from sqlalchemy import select, Table, Column, Integer, String
from sqlalchemy.orm import Query, Session

from app.core.cache.query_cache import QueryCacheManager, cached_query


class TestQueryCacheManager:
    """
    Test query cache manager functionality.
    """
    
    def test_initialization(self):
        """
        Test query cache manager initialization.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=True)
        
        # Verify initialization
        assert cache_manager.enabled is True
        assert cache_manager.prefix == "query_cache"
        assert isinstance(cache_manager.tracked_tables, set)
    
    def test_get_query_hash_string(self):
        """
        Test _get_query_hash method with string query.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=True)
        
        # Get query hash
        query = "SELECT * FROM users WHERE id = 1"
        query_hash = cache_manager._get_query_hash(query)
        
        # Verify query hash
        assert isinstance(query_hash, str)
        assert len(query_hash) == 64  # SHA-256 hash length
    
    def test_get_query_hash_query_object(self):
        """
        Test _get_query_hash method with Query object.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=True)
        
        # Mock Query object
        query = MagicMock(spec=Query)
        query.statement.compile().string = "SELECT * FROM users WHERE id = 1"
        
        # Get query hash
        query_hash = cache_manager._get_query_hash(query)
        
        # Verify query hash
        assert isinstance(query_hash, str)
        assert len(query_hash) == 64  # SHA-256 hash length
    
    def test_get_cache_key(self):
        """
        Test _get_cache_key method.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=True)
        
        # Get cache key
        query_hash = "1234567890abcdef"
        cache_key = cache_manager._get_cache_key(query_hash)
        
        # Verify cache key
        assert cache_key == "query:1234567890abcdef"
    
    def test_get_table_key(self):
        """
        Test _get_table_key method.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=True)
        
        # Get table key
        table_name = "users"
        table_key = cache_manager._get_table_key(table_name)
        
        # Verify table key
        assert table_key == "table:users:updated_at"
    
    def test_get_tables_from_query(self):
        """
        Test _get_tables_from_query method.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=True)
        
        # Create a table
        users = Table(
            "users",
            MagicMock(),
            Column("id", Integer, primary_key=True),
            Column("name", String),
        )
        
        # Create a query
        query = select(users)
        
        # Get tables from query
        tables = cache_manager._get_tables_from_query(query)
        
        # Verify tables
        assert tables == ["users"]
    
    def test_should_use_cache_disabled(self):
        """
        Test _should_use_cache method with disabled cache.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=False)
        
        # Check if cache should be used
        should_use_cache = cache_manager._should_use_cache("1234567890abcdef", ["users"])
        
        # Verify result
        assert should_use_cache is False
    
    def test_should_use_cache_not_in_cache(self):
        """
        Test _should_use_cache method with query not in cache.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=True)
        
        # Mock cache
        cache_manager.cache.exists = MagicMock(return_value=False)
        
        # Check if cache should be used
        should_use_cache = cache_manager._should_use_cache("1234567890abcdef", ["users"])
        
        # Verify result
        assert should_use_cache is False
    
    def test_should_use_cache_in_cache(self):
        """
        Test _should_use_cache method with query in cache.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=True)
        
        # Mock cache
        cache_manager.cache.exists = MagicMock(return_value=True)
        cache_manager.cache.get = MagicMock(return_value=None)
        cache_manager.cache.ttl = MagicMock(return_value=3600)
        
        # Check if cache should be used
        should_use_cache = cache_manager._should_use_cache("1234567890abcdef", ["users"])
        
        # Verify result
        assert should_use_cache is True
    
    def test_update_table_timestamp(self):
        """
        Test _update_table_timestamp method.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=True)
        
        # Mock cache
        cache_manager.cache.set = MagicMock()
        
        # Update table timestamp
        cache_manager._update_table_timestamp("users")
        
        # Verify tracked tables
        assert "users" in cache_manager.tracked_tables
        
        # Verify cache set was called
        cache_manager.cache.set.assert_called_once()
        args, kwargs = cache_manager.cache.set.call_args
        assert args[0] == "table:users:updated_at"
        assert isinstance(args[1], bytes)
        assert kwargs["ttl"] == cache_manager.default_ttl * 2
    
    def test_get_cached_result_disabled(self):
        """
        Test get_cached_result method with disabled cache.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=False)
        
        # Get cached result
        result = cache_manager.get_cached_result("SELECT * FROM users")
        
        # Verify result
        assert result is None
    
    def test_get_cached_result_not_in_cache(self):
        """
        Test get_cached_result method with query not in cache.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=True)
        
        # Mock methods
        cache_manager._get_query_hash = MagicMock(return_value="1234567890abcdef")
        cache_manager._should_use_cache = MagicMock(return_value=False)
        
        # Get cached result
        result = cache_manager.get_cached_result("SELECT * FROM users")
        
        # Verify result
        assert result is None
    
    def test_get_cached_result_in_cache(self):
        """
        Test get_cached_result method with query in cache.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=True)
        
        # Mock methods
        cache_manager._get_query_hash = MagicMock(return_value="1234567890abcdef")
        cache_manager._should_use_cache = MagicMock(return_value=True)
        cache_manager._get_cache_key = MagicMock(return_value="query:1234567890abcdef")
        cache_manager.cache.get = MagicMock(return_value=b'{"id": 1, "name": "Test"}')
        
        # Mock CacheSerializer
        with patch("app.core.cache.query_cache.CacheSerializer") as mock_serializer:
            mock_serializer.deserialize_json.return_value = {"id": 1, "name": "Test"}
            
            # Get cached result
            result = cache_manager.get_cached_result("SELECT * FROM users")
            
            # Verify result
            assert result == {"id": 1, "name": "Test"}
    
    def test_cache_query_result_disabled(self):
        """
        Test cache_query_result method with disabled cache.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=False)
        
        # Cache query result
        result = cache_manager.cache_query_result("SELECT * FROM users", {"id": 1, "name": "Test"})
        
        # Verify result
        assert result is False
    
    def test_cache_query_result(self):
        """
        Test cache_query_result method.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=True)
        
        # Mock methods
        cache_manager._get_query_hash = MagicMock(return_value="1234567890abcdef")
        cache_manager._get_cache_key = MagicMock(return_value="query:1234567890abcdef")
        cache_manager.cache.set = MagicMock(return_value=True)
        
        # Mock CacheSerializer
        with patch("app.core.cache.query_cache.CacheSerializer") as mock_serializer:
            mock_serializer.serialize_json.return_value = b'{"id": 1, "name": "Test"}'
            
            # Cache query result
            result = cache_manager.cache_query_result("SELECT * FROM users", {"id": 1, "name": "Test"})
            
            # Verify result
            assert result is True
    
    def test_invalidate_table_cache(self):
        """
        Test invalidate_table_cache method.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=True)
        
        # Mock methods
        cache_manager._update_table_timestamp = MagicMock()
        
        # Invalidate table cache
        cache_manager.invalidate_table_cache("users")
        
        # Verify _update_table_timestamp was called
        cache_manager._update_table_timestamp.assert_called_once_with("users")
    
    def test_invalidate_query_cache(self):
        """
        Test invalidate_query_cache method.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=True)
        
        # Mock methods
        cache_manager._get_query_hash = MagicMock(return_value="1234567890abcdef")
        cache_manager._get_cache_key = MagicMock(return_value="query:1234567890abcdef")
        cache_manager.cache.delete = MagicMock(return_value=True)
        
        # Invalidate query cache
        result = cache_manager.invalidate_query_cache("SELECT * FROM users")
        
        # Verify result
        assert result is True
    
    def test_clear_all_query_cache(self):
        """
        Test clear_all_query_cache method.
        """
        # Initialize cache manager
        cache_manager = QueryCacheManager(enabled=True)
        
        # Mock methods
        cache_manager.cache.clear_cache = MagicMock(return_value=10)
        
        # Clear all query cache
        result = cache_manager.clear_all_query_cache()
        
        # Verify result
        assert result == 10
    
    def test_cached_query_decorator(self):
        """
        Test cached_query decorator.
        """
        # Mock query cache manager
        with patch("app.core.cache.query_cache.query_cache_manager") as mock_cache_manager, \
             patch("app.core.cache.query_cache.CacheKeyGenerator") as mock_key_generator, \
             patch("app.core.cache.query_cache.CacheSerializer") as mock_serializer, \
             patch("app.core.cache.query_cache.CacheTTLManager") as mock_ttl_manager:
            mock_cache_manager.enabled = True
            mock_cache_manager.default_ttl = 3600
            mock_cache_manager.cache.get = MagicMock(return_value=None)
            mock_cache_manager.cache.set = MagicMock()
            mock_key_generator.generate_key.return_value = "test_key"
            mock_serializer.serialize_json.return_value = b'{"id": 1, "name": "Test"}'
            mock_serializer.deserialize_json.return_value = {"id": 1, "name": "Test"}
            mock_ttl_manager.get_ttl.return_value = 3600
            
            # Define decorated function
            @cached_query()
            def test_function():
                return {"id": 1, "name": "Test"}
            
            # Call decorated function
            result = test_function()
            
            # Verify result
            assert result == {"id": 1, "name": "Test"}
            
            # Verify cache set was called
            mock_cache_manager.cache.set.assert_called_once()
    
    def test_cached_query_decorator_with_ttl(self):
        """
        Test cached_query decorator with TTL.
        """
        # Mock query cache manager
        with patch("app.core.cache.query_cache.query_cache_manager") as mock_cache_manager, \
             patch("app.core.cache.query_cache.CacheKeyGenerator") as mock_key_generator, \
             patch("app.core.cache.query_cache.CacheSerializer") as mock_serializer:
            mock_cache_manager.enabled = True
            mock_cache_manager.cache.get = MagicMock(return_value=None)
            mock_cache_manager.cache.set = MagicMock()
            mock_key_generator.generate_key.return_value = "test_key"
            mock_serializer.serialize_json.return_value = b'{"id": 1, "name": "Test"}'
            
            # Define decorated function
            @cached_query(ttl=1800)
            def test_function():
                return {"id": 1, "name": "Test"}
            
            # Call decorated function
            result = test_function()
            
            # Verify result
            assert result == {"id": 1, "name": "Test"}
            
            # Verify cache set was called with correct TTL
            mock_cache_manager.cache.set.assert_called_once()
            args, kwargs = mock_cache_manager.cache.set.call_args
            assert kwargs["ttl"] == 1800
