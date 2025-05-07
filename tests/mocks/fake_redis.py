"""
Fake Redis implementation for testing.

This module provides a fake Redis implementation that can be used for testing
without requiring a real Redis server. It implements the same interface as the
Redis client used in the application.
"""
import time
from typing import Any, Dict, List, Optional, Union


class FakeRedis:
    """
    Fake Redis implementation for testing.
    
    This class implements the Redis interface used in the application, storing
    data in memory instead of using a real Redis server.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize fake Redis.
        
        Args:
            *args: Arguments (ignored)
            **kwargs: Keyword arguments (ignored)
        """
        self.data: Dict[str, Any] = {}
        self.expires: Dict[str, float] = {}
        self.hash_data: Dict[str, Dict[str, Any]] = {}
        self.connection_pool = None
        
        # Handle decode_responses
        self.decode_responses = kwargs.get('decode_responses', False)
    
    def ping(self) -> bool:
        """
        Ping the server.
        
        Returns:
            bool: Always True
        """
        return True
    
    def _check_expiry(self, key: str) -> bool:
        """
        Check if a key has expired.
        
        Args:
            key: Key to check
            
        Returns:
            bool: True if key exists and has not expired, False otherwise
        """
        if key not in self.expires:
            return key in self.data
        
        if time.time() > self.expires[key]:
            # Key has expired, remove it
            self.data.pop(key, None)
            self.expires.pop(key, None)
            return False
        
        return True
    
    def get(self, key: str) -> Optional[bytes]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[bytes]: Cached value or None if not found
        """
        if not self._check_expiry(key):
            return None
        
        value = self.data.get(key)
        
        # Handle decode_responses
        if self.decode_responses and isinstance(value, bytes):
            return value.decode('utf-8')
        
        return value
    
    def set(
        self, 
        key: str, 
        value: Union[bytes, str], 
        ex: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ex: Expiration time in seconds
            **kwargs: Additional arguments (ignored)
            
        Returns:
            bool: Always True
        """
        # Store value
        self.data[key] = value
        
        # Set expiration if provided
        if ex is not None:
            self.expires[key] = time.time() + ex
        elif key in self.expires:
            # Remove expiration if not provided
            self.expires.pop(key)
        
        return True
    
    def delete(self, *keys: str) -> int:
        """
        Delete keys from cache.
        
        Args:
            *keys: Keys to delete
            
        Returns:
            int: Number of keys deleted
        """
        count = 0
        for key in keys:
            if key in self.data:
                del self.data[key]
                self.expires.pop(key, None)
                count += 1
        return count
    
    def exists(self, key: str) -> int:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            int: 1 if key exists, 0 otherwise
        """
        return 1 if self._check_expiry(key) else 0
    
    def ttl(self, key: str) -> int:
        """
        Get time to live for key.
        
        Args:
            key: Cache key
            
        Returns:
            int: TTL in seconds, -1 if no TTL, -2 if key doesn't exist
        """
        if not self._check_expiry(key):
            return -2
        
        if key not in self.expires:
            return -1
        
        return int(self.expires[key] - time.time())
    
    def expire(self, key: str, ttl: int) -> int:
        """
        Set time to live for key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            int: 1 if successful, 0 if key doesn't exist
        """
        if not self._check_expiry(key):
            return 0
        
        self.expires[key] = time.time() + ttl
        return 1
    
    def incrby(self, key: str, amount: int = 1) -> int:
        """
        Increment value in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment
            
        Returns:
            int: New value
        """
        if not self._check_expiry(key):
            self.data[key] = 0
        
        # Convert to int if needed
        if isinstance(self.data.get(key), bytes):
            self.data[key] = int(self.data[key])
        elif isinstance(self.data.get(key), str):
            self.data[key] = int(self.data[key])
        elif self.data.get(key) is None:
            self.data[key] = 0
        
        self.data[key] += amount
        return self.data[key]
    
    def hget(self, key: str, field: str) -> Optional[bytes]:
        """
        Get field from hash.
        
        Args:
            key: Hash key
            field: Hash field
            
        Returns:
            Optional[bytes]: Field value or None if not found
        """
        if not self._check_expiry(key):
            return None
        
        if key not in self.hash_data:
            return None
        
        value = self.hash_data[key].get(field)
        
        # Handle decode_responses
        if self.decode_responses and isinstance(value, bytes):
            return value.decode('utf-8')
        
        return value
    
    def hset(self, key: str, field: str, value: Union[bytes, str]) -> int:
        """
        Set field in hash.
        
        Args:
            key: Hash key
            field: Hash field
            value: Field value
            
        Returns:
            int: 1 if field is new, 0 if field was updated
        """
        if key not in self.hash_data:
            self.hash_data[key] = {}
            self.data[key] = True  # Mark key as existing
        
        is_new = field not in self.hash_data[key]
        self.hash_data[key][field] = value
        
        return 1 if is_new else 0
    
    def hgetall(self, key: str) -> Dict[str, bytes]:
        """
        Get all fields and values from hash.
        
        Args:
            key: Hash key
            
        Returns:
            Dict[str, bytes]: All fields and values
        """
        if not self._check_expiry(key):
            return {}
        
        if key not in self.hash_data:
            return {}
        
        result = self.hash_data[key].copy()
        
        # Handle decode_responses
        if self.decode_responses:
            for field, value in result.items():
                if isinstance(value, bytes):
                    result[field] = value.decode('utf-8')
        
        return result
    
    def hdel(self, key: str, *fields: str) -> int:
        """
        Delete fields from hash.
        
        Args:
            key: Hash key
            *fields: Fields to delete
            
        Returns:
            int: Number of fields deleted
        """
        if not self._check_expiry(key):
            return 0
        
        if key not in self.hash_data:
            return 0
        
        count = 0
        for field in fields:
            if field in self.hash_data[key]:
                del self.hash_data[key][field]
                count += 1
        
        return count
    
    def info(self) -> Dict[str, Any]:
        """
        Get server information.
        
        Returns:
            Dict[str, Any]: Server information
        """
        return {
            "redis_version": "fakeredis",
            "uptime_in_seconds": "0",
            "connected_clients": "1",
            "used_memory_human": "0B",
            "total_connections_received": "1",
            "total_commands_processed": "1",
        }
    
    def flushall(self) -> bool:
        """
        Delete all keys from all databases.
        
        Returns:
            bool: Always True
        """
        self.data.clear()
        self.expires.clear()
        self.hash_data.clear()
        return True
    
    def flushdb(self) -> bool:
        """
        Delete all keys from the current database.
        
        Returns:
            bool: Always True
        """
        return self.flushall()


class FakeRedisConnectionPool:
    """
    Fake Redis connection pool for testing.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize fake Redis connection pool.
        
        Args:
            *args: Arguments (ignored)
            **kwargs: Keyword arguments (ignored)
        """
        self.connection_kwargs = kwargs
    
    def disconnect(self) -> None:
        """
        Disconnect all connections in the pool.
        """
        pass
