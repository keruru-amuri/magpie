"""
Unit tests for Redis connection.
"""
import pytest
from unittest.mock import patch, MagicMock
import redis

from app.core.cache.connection import (
    RedisConnectionManager,
    RedisCache,
    redis_client
)


class TestRedisConnectionManager:
    """
    Test Redis connection manager functionality.
    """
    
    def test_get_connection(self):
        """
        Test get_connection method.
        """
        # Get connection
        connection = RedisConnectionManager.get_connection()
        
        # Verify connection is created
        assert connection is not None
        assert isinstance(connection, redis.Redis)
    
    def test_get_connection_with_decode(self):
        """
        Test get_connection_with_decode method.
        """
        # Get connection with decode
        connection = RedisConnectionManager.get_connection_with_decode()
        
        # Verify connection is created
        assert connection is not None
        assert isinstance(connection, redis.Redis)
        assert connection.connection_pool.connection_kwargs.get("decode_responses") is True
    
    @patch('app.core.cache.connection.redis_pool')
    def test_close_connections(self, mock_pool):
        """
        Test close_connections method.
        """
        # Close connections
        RedisConnectionManager.close_connections()
        
        # Verify disconnect was called
        mock_pool.disconnect.assert_called_once()


class TestRedisCache:
    """
    Test Redis cache functionality.
    """
    
    @pytest.fixture
    def redis_cache(self):
        """
        Create Redis cache instance for testing.
        """
        return RedisCache(prefix="test")
    
    def test_get_key(self, redis_cache):
        """
        Test _get_key method.
        """
        # Get key
        key = redis_cache._get_key("test_key")
        
        # Verify key
        assert key == "test:test_key"
    
    @patch('app.core.cache.connection.redis_client')
    def test_get(self, mock_redis, redis_cache):
        """
        Test get method.
        """
        # Mock Redis get
        mock_redis.get.return_value = b"test_value"
        
        # Get value
        value = redis_cache.get("test_key")
        
        # Verify value
        assert value == b"test_value"
        mock_redis.get.assert_called_once_with("test:test_key")
    
    @patch('app.core.cache.connection.redis_client')
    def test_get_error(self, mock_redis, redis_cache):
        """
        Test get method with error.
        """
        # Mock Redis get to raise exception
        mock_redis.get.side_effect = redis.RedisError("Connection error")
        
        # Get value
        value = redis_cache.get("test_key")
        
        # Verify value is None
        assert value is None
    
    @patch('app.core.cache.connection.redis_client')
    def test_set_bytes(self, mock_redis, redis_cache):
        """
        Test set method with bytes value.
        """
        # Mock Redis set
        mock_redis.set.return_value = True
        
        # Set value
        result = redis_cache.set("test_key", b"test_value", 60)
        
        # Verify result
        assert result is True
        mock_redis.set.assert_called_once_with("test:test_key", b"test_value", ex=60)
    
    @patch('app.core.cache.connection.redis_client')
    def test_set_string(self, mock_redis, redis_cache):
        """
        Test set method with string value.
        """
        # Mock Redis set
        mock_redis.set.return_value = True
        
        # Set value
        result = redis_cache.set("test_key", "test_value", 60)
        
        # Verify result
        assert result is True
        mock_redis.set.assert_called_once_with("test:test_key", b"test_value", ex=60)
    
    @patch('app.core.cache.connection.redis_client')
    def test_set_error(self, mock_redis, redis_cache):
        """
        Test set method with error.
        """
        # Mock Redis set to raise exception
        mock_redis.set.side_effect = redis.RedisError("Connection error")
        
        # Set value
        result = redis_cache.set("test_key", "test_value")
        
        # Verify result is False
        assert result is False
    
    @patch('app.core.cache.connection.redis_client')
    def test_delete(self, mock_redis, redis_cache):
        """
        Test delete method.
        """
        # Mock Redis delete
        mock_redis.delete.return_value = 1
        
        # Delete value
        result = redis_cache.delete("test_key")
        
        # Verify result
        assert result is True
        mock_redis.delete.assert_called_once_with("test:test_key")
    
    @patch('app.core.cache.connection.redis_client')
    def test_delete_error(self, mock_redis, redis_cache):
        """
        Test delete method with error.
        """
        # Mock Redis delete to raise exception
        mock_redis.delete.side_effect = redis.RedisError("Connection error")
        
        # Delete value
        result = redis_cache.delete("test_key")
        
        # Verify result is False
        assert result is False
    
    @patch('app.core.cache.connection.redis_client')
    def test_exists(self, mock_redis, redis_cache):
        """
        Test exists method.
        """
        # Mock Redis exists
        mock_redis.exists.return_value = 1
        
        # Check if key exists
        result = redis_cache.exists("test_key")
        
        # Verify result
        assert result is True
        mock_redis.exists.assert_called_once_with("test:test_key")
    
    @patch('app.core.cache.connection.redis_client')
    def test_exists_error(self, mock_redis, redis_cache):
        """
        Test exists method with error.
        """
        # Mock Redis exists to raise exception
        mock_redis.exists.side_effect = redis.RedisError("Connection error")
        
        # Check if key exists
        result = redis_cache.exists("test_key")
        
        # Verify result is False
        assert result is False
    
    @patch('app.core.cache.connection.redis_client')
    def test_ttl(self, mock_redis, redis_cache):
        """
        Test ttl method.
        """
        # Mock Redis ttl
        mock_redis.ttl.return_value = 60
        
        # Get TTL
        result = redis_cache.ttl("test_key")
        
        # Verify result
        assert result == 60
        mock_redis.ttl.assert_called_once_with("test:test_key")
    
    @patch('app.core.cache.connection.redis_client')
    def test_ttl_error(self, mock_redis, redis_cache):
        """
        Test ttl method with error.
        """
        # Mock Redis ttl to raise exception
        mock_redis.ttl.side_effect = redis.RedisError("Connection error")
        
        # Get TTL
        result = redis_cache.ttl("test_key")
        
        # Verify result is -2
        assert result == -2
    
    @patch('app.core.cache.connection.redis_client')
    def test_set_ttl(self, mock_redis, redis_cache):
        """
        Test set_ttl method.
        """
        # Mock Redis expire
        mock_redis.expire.return_value = 1
        
        # Set TTL
        result = redis_cache.set_ttl("test_key", 60)
        
        # Verify result
        assert result is True
        mock_redis.expire.assert_called_once_with("test:test_key", 60)
    
    @patch('app.core.cache.connection.redis_client')
    def test_set_ttl_error(self, mock_redis, redis_cache):
        """
        Test set_ttl method with error.
        """
        # Mock Redis expire to raise exception
        mock_redis.expire.side_effect = redis.RedisError("Connection error")
        
        # Set TTL
        result = redis_cache.set_ttl("test_key", 60)
        
        # Verify result is False
        assert result is False
    
    @patch('app.core.cache.connection.redis_client')
    def test_increment(self, mock_redis, redis_cache):
        """
        Test increment method.
        """
        # Mock Redis incrby
        mock_redis.incrby.return_value = 2
        
        # Increment value
        result = redis_cache.increment("test_key", 1)
        
        # Verify result
        assert result == 2
        mock_redis.incrby.assert_called_once_with("test:test_key", 1)
    
    @patch('app.core.cache.connection.redis_client')
    def test_increment_error(self, mock_redis, redis_cache):
        """
        Test increment method with error.
        """
        # Mock Redis incrby to raise exception
        mock_redis.incrby.side_effect = redis.RedisError("Connection error")
        
        # Increment value
        result = redis_cache.increment("test_key", 1)
        
        # Verify result is None
        assert result is None
    
    @patch('app.core.cache.connection.redis_client')
    def test_hash_get(self, mock_redis, redis_cache):
        """
        Test hash_get method.
        """
        # Mock Redis hget
        mock_redis.hget.return_value = b"test_value"
        
        # Get hash field
        result = redis_cache.hash_get("test_key", "test_field")
        
        # Verify result
        assert result == b"test_value"
        mock_redis.hget.assert_called_once_with("test:test_key", "test_field")
    
    @patch('app.core.cache.connection.redis_client')
    def test_hash_get_error(self, mock_redis, redis_cache):
        """
        Test hash_get method with error.
        """
        # Mock Redis hget to raise exception
        mock_redis.hget.side_effect = redis.RedisError("Connection error")
        
        # Get hash field
        result = redis_cache.hash_get("test_key", "test_field")
        
        # Verify result is None
        assert result is None
    
    @patch('app.core.cache.connection.redis_client')
    def test_hash_set_bytes(self, mock_redis, redis_cache):
        """
        Test hash_set method with bytes value.
        """
        # Mock Redis hset
        mock_redis.hset.return_value = 1
        
        # Set hash field
        result = redis_cache.hash_set("test_key", "test_field", b"test_value")
        
        # Verify result
        assert result is True
        mock_redis.hset.assert_called_once_with("test:test_key", "test_field", b"test_value")
    
    @patch('app.core.cache.connection.redis_client')
    def test_hash_set_string(self, mock_redis, redis_cache):
        """
        Test hash_set method with string value.
        """
        # Mock Redis hset
        mock_redis.hset.return_value = 1
        
        # Set hash field
        result = redis_cache.hash_set("test_key", "test_field", "test_value")
        
        # Verify result
        assert result is True
        mock_redis.hset.assert_called_once_with("test:test_key", "test_field", b"test_value")
    
    @patch('app.core.cache.connection.redis_client')
    def test_hash_set_error(self, mock_redis, redis_cache):
        """
        Test hash_set method with error.
        """
        # Mock Redis hset to raise exception
        mock_redis.hset.side_effect = redis.RedisError("Connection error")
        
        # Set hash field
        result = redis_cache.hash_set("test_key", "test_field", "test_value")
        
        # Verify result is False
        assert result is False
    
    @patch('app.core.cache.connection.redis_client')
    def test_hash_delete(self, mock_redis, redis_cache):
        """
        Test hash_delete method.
        """
        # Mock Redis hdel
        mock_redis.hdel.return_value = 1
        
        # Delete hash field
        result = redis_cache.hash_delete("test_key", "test_field")
        
        # Verify result
        assert result is True
        mock_redis.hdel.assert_called_once_with("test:test_key", "test_field")
    
    @patch('app.core.cache.connection.redis_client')
    def test_hash_delete_error(self, mock_redis, redis_cache):
        """
        Test hash_delete method with error.
        """
        # Mock Redis hdel to raise exception
        mock_redis.hdel.side_effect = redis.RedisError("Connection error")
        
        # Delete hash field
        result = redis_cache.hash_delete("test_key", "test_field")
        
        # Verify result is False
        assert result is False
    
    @patch('app.core.cache.connection.redis_client')
    def test_hash_get_all(self, mock_redis, redis_cache):
        """
        Test hash_get_all method.
        """
        # Mock Redis hgetall
        mock_redis.hgetall.return_value = {b"field1": b"value1", b"field2": b"value2"}
        
        # Get all hash fields
        result = redis_cache.hash_get_all("test_key")
        
        # Verify result
        assert result == {b"field1": b"value1", b"field2": b"value2"}
        mock_redis.hgetall.assert_called_once_with("test:test_key")
    
    @patch('app.core.cache.connection.redis_client')
    def test_hash_get_all_error(self, mock_redis, redis_cache):
        """
        Test hash_get_all method with error.
        """
        # Mock Redis hgetall to raise exception
        mock_redis.hgetall.side_effect = redis.RedisError("Connection error")
        
        # Get all hash fields
        result = redis_cache.hash_get_all("test_key")
        
        # Verify result is empty dict
        assert result == {}
    
    @patch('app.core.cache.connection.redis_client')
    def test_clear_cache(self, mock_redis, redis_cache):
        """
        Test clear_cache method.
        """
        # Mock Redis keys and delete
        mock_redis.keys.return_value = ["test:key1", "test:key2"]
        mock_redis.delete.return_value = 2
        
        # Clear cache
        result = redis_cache.clear_cache()
        
        # Verify result
        assert result == 2
        mock_redis.keys.assert_called_once_with("test:*")
        mock_redis.delete.assert_called_once_with("test:key1", "test:key2")
    
    @patch('app.core.cache.connection.redis_client')
    def test_clear_cache_no_keys(self, mock_redis, redis_cache):
        """
        Test clear_cache method with no keys.
        """
        # Mock Redis keys
        mock_redis.keys.return_value = []
        
        # Clear cache
        result = redis_cache.clear_cache()
        
        # Verify result
        assert result == 0
        mock_redis.keys.assert_called_once_with("test:*")
        mock_redis.delete.assert_not_called()
    
    @patch('app.core.cache.connection.redis_client')
    def test_clear_cache_error(self, mock_redis, redis_cache):
        """
        Test clear_cache method with error.
        """
        # Mock Redis keys to raise exception
        mock_redis.keys.side_effect = redis.RedisError("Connection error")
        
        # Clear cache
        result = redis_cache.clear_cache()
        
        # Verify result is 0
        assert result == 0
