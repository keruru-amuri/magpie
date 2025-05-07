"""
Redis mock manager for testing.

This module provides utilities for mocking Redis in tests.
"""
import logging
from typing import Any, Dict, Optional, Union
from unittest.mock import patch

from tests.mocks.fake_redis import FakeRedis, FakeRedisConnectionPool

# Configure logging
logger = logging.getLogger(__name__)


class RedisMockManager:
    """
    Manager for Redis mocking in tests.
    """
    
    _instance = None
    _fake_redis = None
    _patches = []
    
    @classmethod
    def get_instance(cls) -> 'RedisMockManager':
        """
        Get singleton instance.
        
        Returns:
            RedisMockManager: Singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def get_fake_redis(cls) -> FakeRedis:
        """
        Get fake Redis instance.
        
        Returns:
            FakeRedis: Fake Redis instance
        """
        if cls._fake_redis is None:
            cls._fake_redis = FakeRedis()
        return cls._fake_redis
    
    @classmethod
    def enable_redis_mock(cls) -> None:
        """
        Enable Redis mocking.
        
        This method patches the Redis implementation to use the fake Redis.
        """
        # Create fake Redis instance
        fake_redis = cls.get_fake_redis()
        
        # Patch Redis
        cls._patches = [
            patch('redis.Redis', return_value=fake_redis),
            patch('redis.ConnectionPool', return_value=FakeRedisConnectionPool()),
            patch('app.core.cache.connection.redis_client', fake_redis),
            patch('app.core.cache.connection.redis_pool', FakeRedisConnectionPool()),
        ]
        
        # Start patches
        for p in cls._patches:
            p.start()
        
        logger.info("Redis mock enabled")
    
    @classmethod
    def disable_redis_mock(cls) -> None:
        """
        Disable Redis mocking.
        
        This method stops all patches and clears the fake Redis data.
        """
        # Stop patches
        for p in cls._patches:
            p.stop()
        
        # Clear patches
        cls._patches = []
        
        # Clear fake Redis data
        if cls._fake_redis is not None:
            cls._fake_redis.flushall()
        
        logger.info("Redis mock disabled")
    
    @classmethod
    def reset_fake_redis(cls) -> None:
        """
        Reset fake Redis data.
        
        This method clears all data in the fake Redis instance.
        """
        if cls._fake_redis is not None:
            cls._fake_redis.flushall()
        
        logger.info("Fake Redis data reset")
