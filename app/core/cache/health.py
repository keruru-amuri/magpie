"""
Health check functionality for Redis cache.
"""
import logging
import time
from typing import Dict, Tuple

import redis

from app.core.cache.connection import RedisConnectionManager

# Configure logging
logger = logging.getLogger(__name__)


class RedisCacheHealthCheck:
    """
    Health check functionality for Redis cache.
    """

    @staticmethod
    def check_connection() -> Tuple[bool, str]:
        """
        Check if the Redis connection is healthy.

        Returns:
            Tuple[bool, str]: (is_healthy, message)
        """
        try:
            redis_client = RedisConnectionManager.get_connection()
            redis_client.ping()
            return True, "Redis connection is healthy"
        except redis.RedisError as e:
            error_message = f"Redis connection error: {str(e)}"
            logger.error(error_message)
            return False, error_message

    @staticmethod
    def get_info() -> Dict[str, str]:
        """
        Get information about the Redis server.

        Returns:
            Dict[str, str]: Redis server information
        """
        try:
            redis_client = RedisConnectionManager.get_connection()
            info = redis_client.info()

            # Extract relevant information
            return {
                "redis_version": info.get("redis_version", "unknown"),
                "uptime_in_seconds": str(info.get("uptime_in_seconds", "unknown")),
                "connected_clients": str(info.get("connected_clients", "unknown")),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "total_connections_received": str(info.get("total_connections_received", "unknown")),
                "total_commands_processed": str(info.get("total_commands_processed", "unknown")),
            }
        except redis.RedisError as e:
            logger.error(f"Error getting Redis info: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def check_memory() -> Tuple[bool, str]:
        """
        Check if Redis memory usage is within acceptable limits.

        Returns:
            Tuple[bool, str]: (is_healthy, message)
        """
        try:
            redis_client = RedisConnectionManager.get_connection()
            info = redis_client.info()

            # Get memory usage
            used_memory = info.get("used_memory", 0)
            total_system_memory = info.get("total_system_memory", 0)

            # If total_system_memory is not available, we can't calculate percentage
            if not total_system_memory:
                return True, f"Redis memory usage: {info.get('used_memory_human', 'unknown')}"

            # Calculate memory usage percentage
            memory_usage_percent = (used_memory / total_system_memory) * 100

            # Check if memory usage is within acceptable limits
            if memory_usage_percent > 90:
                return False, f"Redis memory usage is critical: {memory_usage_percent:.2f}%"
            elif memory_usage_percent > 75:
                return False, f"Redis memory usage is high: {memory_usage_percent:.2f}%"
            else:
                return True, f"Redis memory usage is acceptable: {memory_usage_percent:.2f}%"
        except redis.RedisError as e:
            error_message = f"Error checking Redis memory: {str(e)}"
            logger.error(error_message)
            return False, error_message

    @staticmethod
    def check_latency() -> Tuple[bool, str]:
        """
        Check Redis latency.

        Returns:
            Tuple[bool, str]: (is_acceptable, message)
        """
        try:
            redis_client = RedisConnectionManager.get_connection()

            # Measure latency for PING command
            start_time = time.time()
            redis_client.ping()
            end_time = time.time()

            ping_latency_ms = (end_time - start_time) * 1000

            # Measure latency for SET and GET commands
            start_time = time.time()
            redis_client.set("health:check:latency", "test")
            redis_client.get("health:check:latency")
            redis_client.delete("health:check:latency")
            end_time = time.time()

            operation_latency_ms = (end_time - start_time) * 1000

            # Check if latency is within acceptable limits
            if ping_latency_ms > 100 or operation_latency_ms > 200:
                return False, (
                    f"Redis latency is high: PING={ping_latency_ms:.2f}ms, "
                    f"SET+GET+DEL={operation_latency_ms:.2f}ms"
                )
            else:
                return True, (
                    f"Redis latency is acceptable: PING={ping_latency_ms:.2f}ms, "
                    f"SET+GET+DEL={operation_latency_ms:.2f}ms"
                )
        except redis.RedisError as e:
            error_message = f"Error checking Redis latency: {str(e)}"
            logger.error(error_message)
            return False, error_message
