"""
Base repository for all repositories in the MAGPIE platform.
"""
import logging
import time
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.cache.connection import RedisCache
from app.core.cache.keys import CacheKeyGenerator
from app.core.cache.query_cache import query_cache_manager, cached_query
from app.core.cache.serialization import CacheSerializer
from app.core.cache.ttl import CacheTTLManager, CacheTTLPolicy
from app.core.db.connection import DatabaseConnectionFactory
from app.core.db.optimizer import query_optimizer, optimized_query
from app.core.monitoring.profiling import profile_function, PerformanceCategory
from app.models.base import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic type hints
T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T]):
    """
    Base repository for all repositories.
    """

    def __init__(
        self,
        model_class_or_session: Union[Type[T], Session],
        session: Optional[Session] = None,
        cache_enabled: bool = True
    ):
        """
        Initialize repository.

        Args:
            model_class_or_session: Model class or SQLAlchemy session
            session: SQLAlchemy session (if first argument is model class)
            cache_enabled: Whether to use cache
        """
        # Handle case when session is passed as first argument
        if isinstance(model_class_or_session, Session):
            self.model_class = None
            self.session = model_class_or_session
            self.cache_enabled = False  # Disable cache when no model class
            self.cache_prefix = "generic"
        else:
            # Normal case with model class
            self.model_class = model_class_or_session
            self.session = session or DatabaseConnectionFactory.get_session()
            self.cache_enabled = cache_enabled
            self.cache_prefix = getattr(self.model_class, "__tablename__", "generic")

        self.cache = RedisCache(prefix="magpie")

    def _get_cache_key(self, id: Union[int, str]) -> str:
        """
        Get cache key for model instance.

        Args:
            id: Model ID

        Returns:
            str: Cache key
        """
        return f"{self.cache_prefix}:{id}"

    def _cache_get(self, id: Union[int, str]) -> Optional[T]:
        """
        Get model instance from cache.

        Args:
            id: Model ID

        Returns:
            Optional[T]: Model instance or None if not found
        """
        if not self.cache_enabled:
            return None

        try:
            cache_key = self._get_cache_key(id)
            cached_data = self.cache.get(cache_key)

            if cached_data:
                return CacheSerializer.deserialize_model(cached_data, self.model_class)

            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return None

    def _cache_set(
        self,
        instance: T,
        ttl_policy: Optional[CacheTTLPolicy] = None
    ) -> bool:
        """
        Set model instance in cache.

        Args:
            instance: Model instance
            ttl_policy: TTL policy

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.cache_enabled or not instance:
            return False

        try:
            cache_key = self._get_cache_key(instance.id)
            serialized_data = CacheSerializer.serialize_model(instance)
            ttl = CacheTTLManager.get_ttl(self.cache_prefix, ttl_policy)

            return self.cache.set(cache_key, serialized_data, ttl)
        except Exception as e:
            logger.error(f"Error setting in cache: {str(e)}")
            return False

    def _cache_delete(self, id: Union[int, str]) -> bool:
        """
        Delete model instance from cache.

        Args:
            id: Model ID

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.cache_enabled:
            return False

        try:
            cache_key = self._get_cache_key(id)
            return self.cache.delete(cache_key)
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False

    @optimized_query
    def get_by_id(self, id: Union[int, str]) -> Optional[T]:
        """
        Get model instance by ID.

        Args:
            id: Model ID

        Returns:
            Optional[T]: Model instance or None if not found
        """
        # Try to get from cache first
        cached_instance = self._cache_get(id)
        if cached_instance:
            return cached_instance

        try:
            # Create query
            query = select(self.model_class).where(self.model_class.id == id)

            # Try to get from query cache
            cached_result = query_cache_manager.get_cached_result(query, self.session)
            if cached_result is not None:
                # Cache in instance cache
                if isinstance(cached_result, list) and cached_result:
                    instance = cached_result[0]
                    self._cache_set(instance)
                    return instance
                elif not isinstance(cached_result, list):
                    self._cache_set(cached_result)
                    return cached_result
                return None

            # Get from database
            start_time = time.time()
            result = self.session.execute(query)
            instance = result.scalar_one_or_none()
            duration_ms = (time.time() - start_time) * 1000

            # Analyze query
            query_optimizer.analyze_query(query, duration_ms)

            # Cache in query cache
            if instance:
                query_cache_manager.cache_query_result(query, instance)

                # Cache in instance cache
                self._cache_set(instance)

            return instance
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model_class.__name__} by ID: {str(e)}")
            return None

    @optimized_query
    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Get all model instances with pagination.

        Args:
            limit: Maximum number of instances to return
            offset: Number of instances to skip

        Returns:
            List[T]: List of model instances
        """
        try:
            # Create query
            query = (
                select(self.model_class)
                .limit(limit)
                .offset(offset)
            )

            # Try to get from query cache
            cached_result = query_cache_manager.get_cached_result(query, self.session)
            if cached_result is not None:
                return cached_result if isinstance(cached_result, list) else [cached_result]

            # Get from database
            start_time = time.time()
            result = self.session.execute(query)
            instances = list(result.scalars().all())
            duration_ms = (time.time() - start_time) * 1000

            # Analyze query
            query_optimizer.analyze_query(query, duration_ms)

            # Cache in query cache
            if instances:
                query_cache_manager.cache_query_result(query, instances)

                # Cache individual instances
                for instance in instances:
                    self._cache_set(instance)

            return instances
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model_class.__name__}: {str(e)}")
            return []

    @profile_function(PerformanceCategory.DATABASE)
    def create(self, data: Union[Dict[str, Any], T]) -> Optional[T]:
        """
        Create model instance.

        Args:
            data: Model data or instance

        Returns:
            Optional[T]: Created model instance or None if error
        """
        try:
            # Create instance if data is a dictionary
            if isinstance(data, dict):
                instance = self.model_class(**data)
            else:
                instance = data

            # Add to session and flush to get ID
            self.session.add(instance)
            self.session.flush()

            # Cache instance
            self._cache_set(instance)

            # Invalidate query cache for this table
            table_name = getattr(self.model_class, "__tablename__", None)
            if table_name:
                query_cache_manager.invalidate_table_cache(table_name)

            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error creating {self.model_class.__name__}: {str(e)}")
            return None

    @profile_function(PerformanceCategory.DATABASE)
    def update(
        self,
        id: Union[int, str],
        data: Dict[str, Any]
    ) -> Optional[T]:
        """
        Update model instance.

        Args:
            id: Model ID
            data: Updated data

        Returns:
            Optional[T]: Updated model instance or None if error
        """
        try:
            # Get instance
            instance = self.get_by_id(id)
            if not instance:
                return None

            # Update instance
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            # Flush changes
            self.session.flush()

            # Update cache
            self._cache_set(instance)

            # Invalidate query cache for this table
            table_name = getattr(self.model_class, "__tablename__", None)
            if table_name:
                query_cache_manager.invalidate_table_cache(table_name)

            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating {self.model_class.__name__}: {str(e)}")
            return None

    @profile_function(PerformanceCategory.DATABASE)
    def delete_by_id(self, id: Union[int, str]) -> bool:
        """
        Delete model instance by ID.

        Args:
            id: Model ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get instance
            instance = self.get_by_id(id)
            if not instance:
                return False

            # Delete instance
            self.session.delete(instance)
            self.session.flush()

            # Delete from cache
            self._cache_delete(id)

            # Invalidate query cache for this table
            table_name = getattr(self.model_class, "__tablename__", None)
            if table_name:
                query_cache_manager.invalidate_table_cache(table_name)

            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error deleting {self.model_class.__name__}: {str(e)}")
            return False

    def commit(self) -> bool:
        """
        Commit changes to database.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error committing changes: {str(e)}")
            return False

    def rollback(self) -> None:
        """
        Rollback changes.
        """
        self.session.rollback()

    def close(self) -> None:
        """
        Close session.
        """
        self.session.close()
