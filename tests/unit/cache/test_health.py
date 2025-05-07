"""
Unit tests for Redis health check.
"""
import pytest
from unittest.mock import patch, MagicMock
import redis
import time

from app.core.cache.health import RedisCacheHealthCheck


class TestRedisCacheHealthCheck:
    """
    Test Redis health check functionality.
    """
    
    @patch('app.core.cache.health.RedisConnectionManager.get_connection')
    def test_check_connection_success(self, mock_get_connection):
        """
        Test check_connection method with successful connection.
        """
        # Mock Redis connection
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_get_connection.return_value = mock_redis
        
        # Check connection
        is_healthy, message = RedisCacheHealthCheck.check_connection()
        
        # Verify connection is healthy
        assert is_healthy is True
        assert "healthy" in message
        mock_redis.ping.assert_called_once()
    
    @patch('app.core.cache.health.RedisConnectionManager.get_connection')
    def test_check_connection_failure(self, mock_get_connection):
        """
        Test check_connection method with failed connection.
        """
        # Mock Redis connection to raise exception
        mock_redis = MagicMock()
        mock_redis.ping.side_effect = redis.RedisError("Connection error")
        mock_get_connection.return_value = mock_redis
        
        # Check connection
        is_healthy, message = RedisCacheHealthCheck.check_connection()
        
        # Verify connection is not healthy
        assert is_healthy is False
        assert "error" in message.lower()
        mock_redis.ping.assert_called_once()
    
    @patch('app.core.cache.health.RedisConnectionManager.get_connection')
    def test_get_info(self, mock_get_connection):
        """
        Test get_info method.
        """
        # Mock Redis connection
        mock_redis = MagicMock()
        mock_redis.info.return_value = {
            "redis_version": "6.2.6",
            "uptime_in_seconds": 3600,
            "connected_clients": 10,
            "used_memory_human": "1M",
            "total_connections_received": 100,
            "total_commands_processed": 1000
        }
        mock_get_connection.return_value = mock_redis
        
        # Get info
        info = RedisCacheHealthCheck.get_info()
        
        # Verify info
        assert info["redis_version"] == "6.2.6"
        assert info["uptime_in_seconds"] == "3600"
        assert info["connected_clients"] == "10"
        assert info["used_memory_human"] == "1M"
        assert info["total_connections_received"] == "100"
        assert info["total_commands_processed"] == "1000"
        mock_redis.info.assert_called_once()
    
    @patch('app.core.cache.health.RedisConnectionManager.get_connection')
    def test_get_info_error(self, mock_get_connection):
        """
        Test get_info method with error.
        """
        # Mock Redis connection to raise exception
        mock_redis = MagicMock()
        mock_redis.info.side_effect = redis.RedisError("Info error")
        mock_get_connection.return_value = mock_redis
        
        # Get info
        info = RedisCacheHealthCheck.get_info()
        
        # Verify error is returned
        assert "error" in info
        mock_redis.info.assert_called_once()
    
    @patch('app.core.cache.health.RedisConnectionManager.get_connection')
    def test_check_memory_acceptable(self, mock_get_connection):
        """
        Test check_memory method with acceptable memory usage.
        """
        # Mock Redis connection
        mock_redis = MagicMock()
        mock_redis.info.return_value = {
            "used_memory": 1000000,
            "total_system_memory": 10000000,
            "used_memory_human": "1M"
        }
        mock_get_connection.return_value = mock_redis
        
        # Check memory
        is_healthy, message = RedisCacheHealthCheck.check_memory()
        
        # Verify memory is acceptable
        assert is_healthy is True
        assert "acceptable" in message
        assert "10.00%" in message
        mock_redis.info.assert_called_once()
    
    @patch('app.core.cache.health.RedisConnectionManager.get_connection')
    def test_check_memory_high(self, mock_get_connection):
        """
        Test check_memory method with high memory usage.
        """
        # Mock Redis connection
        mock_redis = MagicMock()
        mock_redis.info.return_value = {
            "used_memory": 8000000,
            "total_system_memory": 10000000,
            "used_memory_human": "8M"
        }
        mock_get_connection.return_value = mock_redis
        
        # Check memory
        is_healthy, message = RedisCacheHealthCheck.check_memory()
        
        # Verify memory is high
        assert is_healthy is False
        assert "high" in message
        assert "80.00%" in message
        mock_redis.info.assert_called_once()
    
    @patch('app.core.cache.health.RedisConnectionManager.get_connection')
    def test_check_memory_critical(self, mock_get_connection):
        """
        Test check_memory method with critical memory usage.
        """
        # Mock Redis connection
        mock_redis = MagicMock()
        mock_redis.info.return_value = {
            "used_memory": 9500000,
            "total_system_memory": 10000000,
            "used_memory_human": "9.5M"
        }
        mock_get_connection.return_value = mock_redis
        
        # Check memory
        is_healthy, message = RedisCacheHealthCheck.check_memory()
        
        # Verify memory is critical
        assert is_healthy is False
        assert "critical" in message
        assert "95.00%" in message
        mock_redis.info.assert_called_once()
    
    @patch('app.core.cache.health.RedisConnectionManager.get_connection')
    def test_check_memory_no_total(self, mock_get_connection):
        """
        Test check_memory method with no total system memory.
        """
        # Mock Redis connection
        mock_redis = MagicMock()
        mock_redis.info.return_value = {
            "used_memory": 1000000,
            "used_memory_human": "1M"
        }
        mock_get_connection.return_value = mock_redis
        
        # Check memory
        is_healthy, message = RedisCacheHealthCheck.check_memory()
        
        # Verify memory is reported
        assert is_healthy is True
        assert "Redis memory usage: 1M" in message
        mock_redis.info.assert_called_once()
    
    @patch('app.core.cache.health.RedisConnectionManager.get_connection')
    def test_check_memory_error(self, mock_get_connection):
        """
        Test check_memory method with error.
        """
        # Mock Redis connection to raise exception
        mock_redis = MagicMock()
        mock_redis.info.side_effect = redis.RedisError("Memory error")
        mock_get_connection.return_value = mock_redis
        
        # Check memory
        is_healthy, message = RedisCacheHealthCheck.check_memory()
        
        # Verify error is returned
        assert is_healthy is False
        assert "error" in message.lower()
        mock_redis.info.assert_called_once()
    
    @patch('app.core.cache.health.RedisConnectionManager.get_connection')
    @patch('app.core.cache.health.time')
    def test_check_latency_acceptable(self, mock_time, mock_get_connection):
        """
        Test check_latency method with acceptable latency.
        """
        # Mock time
        mock_time.time.side_effect = [0, 0.01, 0.02, 0.05]
        
        # Mock Redis connection
        mock_redis = MagicMock()
        mock_get_connection.return_value = mock_redis
        
        # Check latency
        is_acceptable, message = RedisCacheHealthCheck.check_latency()
        
        # Verify latency is acceptable
        assert is_acceptable is True
        assert "acceptable" in message
        assert "PING=10.00ms" in message
        assert "SET+GET+DEL=30.00ms" in message
        mock_redis.ping.assert_called_once()
        mock_redis.set.assert_called_once_with("health:check:latency", "test")
        mock_redis.get.assert_called_once_with("health:check:latency")
        mock_redis.delete.assert_called_once_with("health:check:latency")
    
    @patch('app.core.cache.health.RedisConnectionManager.get_connection')
    @patch('app.core.cache.health.time')
    def test_check_latency_high(self, mock_time, mock_get_connection):
        """
        Test check_latency method with high latency.
        """
        # Mock time
        mock_time.time.side_effect = [0, 0.2, 0.3, 0.5]
        
        # Mock Redis connection
        mock_redis = MagicMock()
        mock_get_connection.return_value = mock_redis
        
        # Check latency
        is_acceptable, message = RedisCacheHealthCheck.check_latency()
        
        # Verify latency is high
        assert is_acceptable is False
        assert "high" in message
        assert "PING=200.00ms" in message
        assert "SET+GET+DEL=200.00ms" in message
        mock_redis.ping.assert_called_once()
        mock_redis.set.assert_called_once_with("health:check:latency", "test")
        mock_redis.get.assert_called_once_with("health:check:latency")
        mock_redis.delete.assert_called_once_with("health:check:latency")
    
    @patch('app.core.cache.health.RedisConnectionManager.get_connection')
    def test_check_latency_error(self, mock_get_connection):
        """
        Test check_latency method with error.
        """
        # Mock Redis connection to raise exception
        mock_redis = MagicMock()
        mock_redis.ping.side_effect = redis.RedisError("Latency error")
        mock_get_connection.return_value = mock_redis
        
        # Check latency
        is_acceptable, message = RedisCacheHealthCheck.check_latency()
        
        # Verify error is returned
        assert is_acceptable is False
        assert "error" in message.lower()
        mock_redis.ping.assert_called_once()
