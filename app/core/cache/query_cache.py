"""
Query cache manager for the MAGPIE platform.

This module provides functionality for caching database query results
to improve performance and reduce database load.
"""

import hashlib
import inspect
import json
import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union, cast

from sqlalchemy import Column, Table, inspect as sa_inspect
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql import Select

from app.core.cache.connection import RedisCache
from app.core.cache.keys import CacheKeyGenerator
from app.core.cache.serialization import CacheSerializer
from app.core.cache.ttl import CacheTTLManager, CacheTTLPolicy
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for function return type
F = TypeVar('F', bound=Callable[..., Any])


class QueryCacheManager:
    """
    Manager for caching database query results.
    """

    def __init__(
        self,
        prefix: str = "query_cache",
        enabled: bool = True,
        default_ttl: int = settings.CACHE_TTL_MEDIUM,
    ):
        """
        Initialize query cache manager.

        Args:
            prefix: Cache key prefix
            enabled: Whether caching is enabled
            default_ttl: Default TTL in seconds
        """
        self.prefix = prefix
        self.enabled = enabled
        self.default_ttl = default_ttl
        self.cache = RedisCache(prefix=prefix)
        self.logger = logger

        # Set of tables that should invalidate cache when modified
        self.tracked_tables: Set[str] = set()

    def _get_query_hash(self, query: Union[Query, Select, str]) -> str:
        """
        Generate a hash for a query.

        Args:
            query: SQLAlchemy query or SQL string

        Returns:
            str: Query hash
        """
        if isinstance(query, str):
            # SQL string
            query_str = query
        elif hasattr(query, 'statement'):
            # SQLAlchemy Query object
            query_str = str(query.statement.compile(
                compile_kwargs={"literal_binds": True}
            ))
        else:
            # SQLAlchemy Select object
            query_str = str(query.compile(
                compile_kwargs={"literal_binds": True}
            ))

        # Generate hash
        hash_obj = hashlib.sha256(query_str.encode('utf-8'))
        return hash_obj.hexdigest()

    def _get_cache_key(self, query_hash: str) -> str:
        """
        Generate a cache key for a query hash.

        Args:
            query_hash: Query hash

        Returns:
            str: Cache key
        """
        return f"query:{query_hash}"

    def _get_table_key(self, table_name: str) -> str:
        """
        Generate a cache key for a table's last update timestamp.

        Args:
            table_name: Table name

        Returns:
            str: Cache key
        """
        return f"table:{table_name}:updated_at"

    def _get_tables_from_query(self, query: Union[Query, Select]) -> List[str]:
        """
        Extract table names from a query.

        Args:
            query: SQLAlchemy query

        Returns:
            List[str]: List of table names
        """
        tables = []

        if hasattr(query, 'statement'):
            # SQLAlchemy Query object
            statement = query.statement
        else:
            # SQLAlchemy Select object
            statement = query

        # Extract tables from statement
        for table in statement.froms:
            if isinstance(table, Table):
                tables.append(table.name)

        return tables

    def _should_use_cache(self, query_hash: str, tables: List[str]) -> bool:
        """
        Check if cache should be used for a query.

        Args:
            query_hash: Query hash
            tables: List of tables in the query

        Returns:
            bool: Whether to use cache
        """
        if not self.enabled:
            return False

        # Check if query result is in cache
        cache_key = self._get_cache_key(query_hash)
        if not self.cache.exists(cache_key):
            return False

        # Check if any table has been updated since the query was cached
        for table in tables:
            table_key = self._get_table_key(table)
            table_updated_at = self.cache.get(table_key)

            if table_updated_at is None:
                # Table update time not tracked, assume cache is valid
                continue

            # Get query cache timestamp
            query_cached_at = self.cache.ttl(cache_key)
            if query_cached_at == -1:
                # Query has no TTL, assume cache is valid
                continue

            # Convert bytes to float
            table_updated_at_float = float(table_updated_at.decode('utf-8'))

            # Check if table was updated after query was cached
            if table_updated_at_float > time.time() - query_cached_at:
                return False

        return True

    def _update_table_timestamp(self, table_name: str) -> None:
        """
        Update the last update timestamp for a table.

        Args:
            table_name: Table name
        """
        if not self.enabled:
            return

        # Add table to tracked tables
        self.tracked_tables.add(table_name)

        # Update table timestamp
        table_key = self._get_table_key(table_name)
        self.cache.set(table_key, str(time.time()).encode('utf-8'), ttl=self.default_ttl * 2)

    def get_cached_result(
        self,
        query: Union[Query, Select, str],
        session: Optional[Session] = None,
    ) -> Optional[Any]:
        """
        Get cached result for a query.

        Args:
            query: SQLAlchemy query or SQL string
            session: SQLAlchemy session (required for Query objects)

        Returns:
            Optional[Any]: Cached result or None if not found
        """
        if not self.enabled:
            return None

        # Generate query hash
        query_hash = self._get_query_hash(query)

        # Get tables from query
        if isinstance(query, str):
            # SQL string, can't extract tables
            tables = []
        else:
            tables = self._get_tables_from_query(query)

        # Check if cache should be used
        if not self._should_use_cache(query_hash, tables):
            return None

        # Get cached result
        cache_key = self._get_cache_key(query_hash)
        cached_data = self.cache.get(cache_key)

        if cached_data is None:
            return None

        try:
            # Deserialize cached data
            result = CacheSerializer.deserialize_json(cached_data)

            # Convert to model instances if session is provided
            if session is not None and isinstance(query, Query):
                # Get model class from query
                mapper = query._bind_mapper()
                if mapper is not None:
                    model_class = mapper.class_

                    # Convert dictionaries to model instances
                    if isinstance(result, list):
                        result = [model_class(**item) for item in result]
                    elif isinstance(result, dict):
                        result = model_class(**result)

            return result
        except Exception as e:
            self.logger.error(f"Error deserializing cached query result: {str(e)}")
            return None

    def cache_query_result(
        self,
        query: Union[Query, Select, str],
        result: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Cache result for a query.

        Args:
            query: SQLAlchemy query or SQL string
            result: Query result
            ttl: TTL in seconds

        Returns:
            bool: Whether caching was successful
        """
        if not self.enabled:
            return False

        # Generate query hash
        query_hash = self._get_query_hash(query)

        # Serialize result
        try:
            # Convert model instances to dictionaries
            if hasattr(result, 'to_dict'):
                # Single model instance
                serialized_result = result.to_dict()
            elif isinstance(result, list) and all(hasattr(item, 'to_dict') for item in result):
                # List of model instances
                serialized_result = [item.to_dict() for item in result]
            else:
                # Other result types
                serialized_result = result

            # Serialize to JSON
            serialized_data = CacheSerializer.serialize_json(serialized_result)
        except Exception as e:
            self.logger.error(f"Error serializing query result: {str(e)}")
            return False

        # Cache result
        cache_key = self._get_cache_key(query_hash)
        return self.cache.set(
            cache_key,
            serialized_data,
            ttl=ttl or self.default_ttl,
        )

    def invalidate_table_cache(self, table_name: str) -> None:
        """
        Invalidate cache for a table.

        Args:
            table_name: Table name
        """
        if not self.enabled:
            return

        # Update table timestamp
        self._update_table_timestamp(table_name)

    def invalidate_query_cache(self, query: Union[Query, Select, str]) -> bool:
        """
        Invalidate cache for a query.

        Args:
            query: SQLAlchemy query or SQL string

        Returns:
            bool: Whether invalidation was successful
        """
        if not self.enabled:
            return False

        # Generate query hash
        query_hash = self._get_query_hash(query)

        # Delete cached result
        cache_key = self._get_cache_key(query_hash)
        return self.cache.delete(cache_key)

    def clear_all_query_cache(self) -> int:
        """
        Clear all query cache.

        Returns:
            int: Number of keys deleted
        """
        if not self.enabled:
            return 0

        # Clear all query cache
        return self.cache.clear_cache("query:*")


# Create a global query cache manager instance
query_cache_manager = QueryCacheManager(
    enabled=settings.ENVIRONMENT != "testing",
)


def cached_query(
    ttl: Optional[int] = None,
    ttl_policy: Optional[CacheTTLPolicy] = None,
    key_prefix: Optional[str] = None,
) -> Callable[[F], F]:
    """
    Decorator for caching query results.

    Args:
        ttl: TTL in seconds
        ttl_policy: TTL policy
        key_prefix: Cache key prefix

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip caching if disabled
            if not query_cache_manager.enabled:
                return func(*args, **kwargs)

            # Get session from args or kwargs
            session = None
            for arg in args:
                if isinstance(arg, Session):
                    session = arg
                    break

            if session is None:
                session = kwargs.get('session')

            # Generate cache key
            if key_prefix:
                # Use provided key prefix
                prefix = key_prefix
            else:
                # Use function name as key prefix
                prefix = f"{func.__module__}.{func.__qualname__}"

            cache_key = CacheKeyGenerator.generate_key(prefix, *args, **kwargs)

            # Get TTL
            if ttl is not None:
                # Use provided TTL
                cache_ttl = ttl
            elif ttl_policy is not None:
                # Use TTL policy
                cache_ttl = CacheTTLManager.get_ttl("query", ttl_policy)
            else:
                # Use default TTL
                cache_ttl = query_cache_manager.default_ttl

            # Try to get from cache
            cached_data = query_cache_manager.cache.get(cache_key)
            if cached_data is not None:
                try:
                    # Deserialize cached data
                    return CacheSerializer.deserialize_json(cached_data)
                except Exception as e:
                    logger.error(f"Error deserializing cached data: {str(e)}")

            # Call original function
            result = func(*args, **kwargs)

            # Cache result
            try:
                serialized_data = CacheSerializer.serialize_json(result)
                query_cache_manager.cache.set(cache_key, serialized_data, ttl=cache_ttl)
            except Exception as e:
                logger.error(f"Error caching query result: {str(e)}")

            return result

        return cast(F, wrapper)

    return decorator
