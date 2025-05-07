"""
Redis connection module for the MAGPIE platform.
"""
import logging
import time
from typing import Any, Dict, Optional, Union, Callable, TypeVar

import redis
from redis import Redis
from redis.connection import ConnectionPool
from functools import wraps

from app.core.config import settings, EnvironmentType

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for function return type
F = TypeVar('F', bound=Callable[..., Any])


def profile_cache_operation(operation: str) -> Callable[[F], F]:
    """
    Decorator for profiling cache operations.

    Args:
        operation: Cache operation name

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(self, key: str, *args, **kwargs):
            # Skip profiling in testing environment
            if settings.ENVIRONMENT == EnvironmentType.TESTING or not settings.PROFILE_CACHE_OPERATIONS:
                return func(self, key, *args, **kwargs)

            # Record start time
            start_time = time.time()

            try:
                # Call original function
                result = func(self, key, *args, **kwargs)

                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000

                # Record cache operation
                try:
                    from app.core.monitoring.profiling import record_cache_operation

                    # Determine if it's a hit or miss for get operations
                    hit = None
                    if operation == "get" and result is not None:
                        hit = True
                    elif operation == "get" and result is None:
                        hit = False

                    # Record operation
                    record_cache_operation(
                        operation=operation,
                        key=self._get_key(key),
                        duration_ms=duration_ms,
                        hit=hit,
                    )
                except ImportError:
                    # Profiling module not available
                    pass

                return result
            except Exception as e:
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000

                # Record cache operation
                try:
                    from app.core.monitoring.profiling import record_cache_operation

                    # Record operation
                    record_cache_operation(
                        operation=operation,
                        key=self._get_key(key),
                        duration_ms=duration_ms,
                        hit=None,
                    )
                except ImportError:
                    # Profiling module not available
                    pass

                # Re-raise exception
                raise

        return wrapper

    return decorator

# Create Redis connection pool
redis_pool = ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD or None,
    db=settings.REDIS_DB,
    decode_responses=False,  # Keep binary data as is
    socket_timeout=settings.REDIS_TIMEOUT,
    socket_connect_timeout=settings.REDIS_TIMEOUT,
    retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
    health_check_interval=settings.REDIS_HEALTH_CHECK_INTERVAL,
    max_connections=settings.REDIS_MAX_CONNECTIONS,
)


class RedisConnectionManager:
    """
    Manager for Redis connections.
    """

    @staticmethod
    def get_connection() -> Redis:
        """
        Get a Redis connection from the pool.

        Returns:
            Redis: Redis connection
        """
        return Redis(connection_pool=redis_pool)

    @staticmethod
    def get_connection_with_decode() -> Redis:
        """
        Get a Redis connection with string decoding.

        Returns:
            Redis: Redis connection with decode_responses=True
        """
        return Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD or None,
            db=settings.REDIS_DB,
            decode_responses=True,  # Decode responses to strings
            socket_timeout=settings.REDIS_TIMEOUT,
            socket_connect_timeout=settings.REDIS_TIMEOUT,
            retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
            health_check_interval=settings.REDIS_HEALTH_CHECK_INTERVAL,
        )

    @staticmethod
    def close_connections() -> None:
        """
        Close all connections in the pool.
        """
        redis_pool.disconnect()
        logger.info("All Redis connections closed")


# Create a global Redis client for convenience
redis_client = RedisConnectionManager.get_connection()


class RedisCache:
    """
    Redis cache implementation.
    """

    def __init__(self, prefix: str = "magpie"):
        """
        Initialize Redis cache.

        Args:
            prefix: Key prefix for namespacing
        """
        self.prefix = prefix
        self.redis = redis_client

    def _get_key(self, key: str) -> str:
        """
        Get prefixed key.

        Args:
            key: Original key

        Returns:
            str: Prefixed key
        """
        return f"{self.prefix}:{key}"

    @profile_cache_operation("get")
    def get(self, key: str) -> Optional[bytes]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Optional[bytes]: Cached value or None if not found
        """
        try:
            return self.redis.get(self._get_key(key))
        except redis.RedisError as e:
            logger.error(f"Redis error in get: {str(e)}")
            return None

    @profile_cache_operation("set")
    def set(
        self,
        key: str,
        value: Union[bytes, str],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert string to bytes if needed
            if isinstance(value, str):
                value = value.encode('utf-8')

            return self.redis.set(
                self._get_key(key),
                value,
                ex=ttl or settings.CACHE_TTL_DEFAULT
            )
        except redis.RedisError as e:
            logger.error(f"Redis error in set: {str(e)}")
            return False

    @profile_cache_operation("delete")
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            return bool(self.redis.delete(self._get_key(key)))
        except redis.RedisError as e:
            logger.error(f"Redis error in delete: {str(e)}")
            return False

    @profile_cache_operation("exists")
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            bool: True if key exists, False otherwise
        """
        try:
            return bool(self.redis.exists(self._get_key(key)))
        except redis.RedisError as e:
            logger.error(f"Redis error in exists: {str(e)}")
            return False

    def ttl(self, key: str) -> int:
        """
        Get time to live for key.

        Args:
            key: Cache key

        Returns:
            int: TTL in seconds, -1 if no TTL, -2 if key doesn't exist
        """
        try:
            return self.redis.ttl(self._get_key(key))
        except redis.RedisError as e:
            logger.error(f"Redis error in ttl: {str(e)}")
            return -2

    def set_ttl(self, key: str, ttl: int) -> bool:
        """
        Set time to live for key.

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            return bool(self.redis.expire(self._get_key(key), ttl))
        except redis.RedisError as e:
            logger.error(f"Redis error in set_ttl: {str(e)}")
            return False

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment value in cache.

        Args:
            key: Cache key
            amount: Amount to increment

        Returns:
            Optional[int]: New value or None if error
        """
        try:
            return self.redis.incrby(self._get_key(key), amount)
        except redis.RedisError as e:
            logger.error(f"Redis error in increment: {str(e)}")
            return None

    def hash_get(self, key: str, field: str) -> Optional[bytes]:
        """
        Get field from hash.

        Args:
            key: Hash key
            field: Hash field

        Returns:
            Optional[bytes]: Field value or None if not found
        """
        try:
            return self.redis.hget(self._get_key(key), field)
        except redis.RedisError as e:
            logger.error(f"Redis error in hash_get: {str(e)}")
            return None

    def hash_set(self, key: str, field: str, value: Union[bytes, str]) -> bool:
        """
        Set field in hash.

        Args:
            key: Hash key
            field: Hash field
            value: Field value

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert string to bytes if needed
            if isinstance(value, str):
                value = value.encode('utf-8')

            return bool(self.redis.hset(self._get_key(key), field, value))
        except redis.RedisError as e:
            logger.error(f"Redis error in hash_set: {str(e)}")
            return False

    def hash_delete(self, key: str, field: str) -> bool:
        """
        Delete field from hash.

        Args:
            key: Hash key
            field: Hash field

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            return bool(self.redis.hdel(self._get_key(key), field))
        except redis.RedisError as e:
            logger.error(f"Redis error in hash_delete: {str(e)}")
            return False

    def hash_get_all(self, key: str) -> Dict[bytes, bytes]:
        """
        Get all fields and values from hash.

        Args:
            key: Hash key

        Returns:
            Dict[bytes, bytes]: All fields and values
        """
        try:
            return self.redis.hgetall(self._get_key(key))
        except redis.RedisError as e:
            logger.error(f"Redis error in hash_get_all: {str(e)}")
            return {}

    def clear_cache(self, pattern: str = "*") -> int:
        """
        Clear cache keys matching pattern.

        Args:
            pattern: Key pattern to match

        Returns:
            int: Number of keys deleted
        """
        try:
            keys = self.redis.keys(self._get_key(pattern))
            if keys:
                return self.redis.delete(*keys)
            return 0
        except redis.RedisError as e:
            logger.error(f"Redis error in clear_cache: {str(e)}")
            return 0
