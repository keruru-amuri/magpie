"""
Context window monitoring for the MAGPIE platform.
"""
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app.core.cache.connection import RedisCache
from app.core.db.connection import DatabaseConnectionFactory
from app.models.context import ContextWindow, ContextItem, ContextType, ContextPriority

# Configure logging
logger = logging.getLogger(__name__)


class ContextWindowMetrics:
    """
    Metrics collection for context window usage.
    """

    def __init__(self, session: Optional[Session] = None, cache: Optional[RedisCache] = None):
        """
        Initialize context window metrics.

        Args:
            session: SQLAlchemy session
            cache: Redis cache
        """
        self.session = session or DatabaseConnectionFactory.get_session()
        self.cache = cache or RedisCache(prefix="context_metrics")
        self.cache_ttl = 3600  # 1 hour

    def record_window_usage(self, window_id: int, tokens_used: int) -> None:
        """
        Record context window usage.

        Args:
            window_id: Context window ID
            tokens_used: Number of tokens used
        """
        try:
            # Get current timestamp
            timestamp = datetime.now(timezone.utc).isoformat()

            # Record in Redis
            window_key = f"window:{window_id}:usage"
            usage_data = {
                "timestamp": timestamp,
                "tokens_used": tokens_used
            }

            # Store as a list of recent usages (limited to 100 entries)
            self.cache.lpush(window_key, usage_data)
            self.cache.ltrim(window_key, 0, 99)
            self.cache.expire(window_key, self.cache_ttl)

            # Update global metrics
            self._update_global_metrics(tokens_used)
        except Exception as e:
            logger.error(f"Error recording window usage: {str(e)}")

    def record_pruning_event(
        self,
        window_id: int,
        strategy_name: str,
        tokens_before: int,
        tokens_after: int,
        items_removed: int
    ) -> None:
        """
        Record a pruning event.

        Args:
            window_id: Context window ID
            strategy_name: Name of the pruning strategy used
            tokens_before: Number of tokens before pruning
            tokens_after: Number of tokens after pruning
            items_removed: Number of items removed
        """
        try:
            # Get current timestamp
            timestamp = datetime.now(timezone.utc).isoformat()

            # Record in Redis
            pruning_key = f"window:{window_id}:pruning"
            pruning_data = {
                "timestamp": timestamp,
                "strategy": strategy_name,
                "tokens_before": tokens_before,
                "tokens_after": tokens_after,
                "tokens_removed": tokens_before - tokens_after,
                "items_removed": items_removed
            }

            # Store as a list of recent pruning events (limited to 50 entries)
            self.cache.lpush(pruning_key, pruning_data)
            self.cache.ltrim(pruning_key, 0, 49)
            self.cache.expire(pruning_key, self.cache_ttl)

            # Update global pruning metrics
            self._update_global_pruning_metrics(
                strategy_name,
                tokens_before - tokens_after,
                items_removed
            )
        except Exception as e:
            logger.error(f"Error recording pruning event: {str(e)}")

    def _update_global_metrics(self, tokens_used: int) -> None:
        """
        Update global context window metrics.

        Args:
            tokens_used: Number of tokens used
        """
        try:
            # Update total tokens used
            total_key = "global:total_tokens_used"
            self.cache.incrby(total_key, tokens_used)
            self.cache.expire(total_key, self.cache_ttl)

            # Update request count
            request_key = "global:request_count"
            self.cache.incr(request_key)
            self.cache.expire(request_key, self.cache_ttl)

            # Update average tokens per request
            avg_key = "global:avg_tokens_per_request"
            total_tokens = int(self.cache.get(total_key) or 0)
            request_count = int(self.cache.get(request_key) or 1)
            avg_tokens = total_tokens / request_count
            self.cache.set(avg_key, avg_tokens)
            self.cache.expire(avg_key, self.cache_ttl)

            # Record timestamp of last update
            last_update_key = "global:last_update"
            self.cache.set(last_update_key, datetime.now(timezone.utc).isoformat())
            self.cache.expire(last_update_key, self.cache_ttl)
        except Exception as e:
            logger.error(f"Error updating global metrics: {str(e)}")

    def _update_global_pruning_metrics(
        self,
        strategy_name: str,
        tokens_removed: int,
        items_removed: int
    ) -> None:
        """
        Update global pruning metrics.

        Args:
            strategy_name: Name of the pruning strategy used
            tokens_removed: Number of tokens removed
            items_removed: Number of items removed
        """
        try:
            # Update total pruning count
            pruning_count_key = "global:pruning_count"
            self.cache.incr(pruning_count_key)
            self.cache.expire(pruning_count_key, self.cache_ttl)

            # Update total tokens removed
            tokens_removed_key = "global:tokens_removed"
            self.cache.incrby(tokens_removed_key, tokens_removed)
            self.cache.expire(tokens_removed_key, self.cache_ttl)

            # Update total items removed
            items_removed_key = "global:items_removed"
            self.cache.incrby(items_removed_key, items_removed)
            self.cache.expire(items_removed_key, self.cache_ttl)

            # Update strategy-specific metrics
            strategy_count_key = f"strategy:{strategy_name}:count"
            self.cache.incr(strategy_count_key)
            self.cache.expire(strategy_count_key, self.cache_ttl)

            strategy_tokens_key = f"strategy:{strategy_name}:tokens_removed"
            self.cache.incrby(strategy_tokens_key, tokens_removed)
            self.cache.expire(strategy_tokens_key, self.cache_ttl)

            strategy_items_key = f"strategy:{strategy_name}:items_removed"
            self.cache.incrby(strategy_items_key, items_removed)
            self.cache.expire(strategy_items_key, self.cache_ttl)
        except Exception as e:
            logger.error(f"Error updating global pruning metrics: {str(e)}")

    def get_window_metrics(self, window_id: int) -> Dict[str, Any]:
        """
        Get metrics for a specific context window.

        Args:
            window_id: Context window ID

        Returns:
            Dict[str, Any]: Window metrics
        """
        try:
            # Get window from database
            window = self.session.get(ContextWindow, window_id)
            if not window:
                return {"error": f"Window {window_id} not found"}

            # Get usage history from Redis
            usage_key = f"window:{window_id}:usage"
            usage_history = self.cache.lrange(usage_key, 0, -1) or []

            # Get pruning history from Redis
            pruning_key = f"window:{window_id}:pruning"
            pruning_history = self.cache.lrange(pruning_key, 0, -1) or []

            # Get current window stats from database
            query = (
                select(
                    func.count(ContextItem.id).label("total_items"),
                    func.sum(ContextItem.token_count).label("total_tokens"),
                    func.avg(ContextItem.token_count).label("avg_tokens_per_item")
                )
                .where(
                    ContextItem.context_window_id == window_id,
                    ContextItem.is_included == True
                )
            )
            result = self.session.execute(query).first()

            # Get item type distribution
            type_query = (
                select(
                    ContextItem.context_type,
                    func.count(ContextItem.id).label("count"),
                    func.sum(ContextItem.token_count).label("tokens")
                )
                .where(
                    ContextItem.context_window_id == window_id,
                    ContextItem.is_included == True
                )
                .group_by(ContextItem.context_type)
            )
            type_results = self.session.execute(type_query).all()
            type_distribution = {
                str(r.context_type): {"count": r.count, "tokens": r.tokens}
                for r in type_results
            }

            # Get priority distribution
            priority_query = (
                select(
                    ContextItem.priority,
                    func.count(ContextItem.id).label("count"),
                    func.sum(ContextItem.token_count).label("tokens")
                )
                .where(
                    ContextItem.context_window_id == window_id,
                    ContextItem.is_included == True
                )
                .group_by(ContextItem.priority)
            )
            priority_results = self.session.execute(priority_query).all()
            priority_distribution = {
                str(r.priority): {"count": r.count, "tokens": r.tokens}
                for r in priority_results
            }

            # Compile metrics
            return {
                "window_id": window_id,
                "conversation_id": window.conversation_id,
                "max_tokens": window.max_tokens,
                "current_tokens": window.current_tokens,
                "is_active": window.is_active,
                "created_at": window.created_at.isoformat() if window.created_at else None,
                "updated_at": window.updated_at.isoformat() if window.updated_at else None,
                "usage_history": usage_history,
                "pruning_history": pruning_history,
                "current_stats": {
                    "total_items": result.total_items or 0,
                    "total_tokens": result.total_tokens or 0,
                    "avg_tokens_per_item": result.avg_tokens_per_item or 0,
                    "token_usage_percent": (
                        (window.current_tokens / window.max_tokens) * 100
                        if window.max_tokens > 0 else 0
                    ),
                    "type_distribution": type_distribution,
                    "priority_distribution": priority_distribution
                }
            }
        except Exception as e:
            logger.error(f"Error getting window metrics: {str(e)}")
            return {"error": str(e)}

    def get_global_metrics(self) -> Dict[str, Any]:
        """
        Get global context window metrics.

        Returns:
            Dict[str, Any]: Global metrics
        """
        try:
            # Get global metrics from Redis
            total_tokens = int(self.cache.get("global:total_tokens_used") or 0)
            request_count = int(self.cache.get("global:request_count") or 0)
            avg_tokens = float(self.cache.get("global:avg_tokens_per_request") or 0)
            last_update = self.cache.get("global:last_update")

            # Get pruning metrics
            pruning_count = int(self.cache.get("global:pruning_count") or 0)
            tokens_removed = int(self.cache.get("global:tokens_removed") or 0)
            items_removed = int(self.cache.get("global:items_removed") or 0)

            # Get strategy metrics
            strategy_metrics = {}
            strategy_keys = self.cache.keys("strategy:*:count")
            for key in strategy_keys:
                strategy_name = key.split(":")[1]
                count = int(self.cache.get(f"strategy:{strategy_name}:count") or 0)
                tokens = int(self.cache.get(f"strategy:{strategy_name}:tokens_removed") or 0)
                items = int(self.cache.get(f"strategy:{strategy_name}:items_removed") or 0)
                strategy_metrics[strategy_name] = {
                    "count": count,
                    "tokens_removed": tokens,
                    "items_removed": items
                }

            # Get database metrics
            window_query = (
                select(
                    func.count(ContextWindow.id).label("total_windows"),
                    func.sum(ContextWindow.current_tokens).label("total_tokens"),
                    func.avg(ContextWindow.current_tokens).label("avg_tokens_per_window")
                )
            )
            window_result = self.session.execute(window_query).first()

            item_query = (
                select(
                    func.count(ContextItem.id).label("total_items"),
                    func.sum(ContextItem.token_count).label("total_tokens"),
                    func.avg(ContextItem.token_count).label("avg_tokens_per_item")
                )
                .where(ContextItem.is_included == True)
            )
            item_result = self.session.execute(item_query).first()

            # Compile metrics
            return {
                "runtime_metrics": {
                    "total_tokens_used": total_tokens,
                    "request_count": request_count,
                    "avg_tokens_per_request": avg_tokens,
                    "last_update": last_update
                },
                "pruning_metrics": {
                    "pruning_count": pruning_count,
                    "tokens_removed": tokens_removed,
                    "items_removed": items_removed,
                    "strategies": strategy_metrics
                },
                "database_metrics": {
                    "windows": {
                        "total_count": window_result.total_windows or 0,
                        "total_tokens": window_result.total_tokens or 0,
                        "avg_tokens_per_window": window_result.avg_tokens_per_window or 0
                    },
                    "items": {
                        "total_count": item_result.total_items or 0,
                        "total_tokens": item_result.total_tokens or 0,
                        "avg_tokens_per_item": item_result.avg_tokens_per_item or 0
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error getting global metrics: {str(e)}")
            return {"error": str(e)}

    def get_window_health(self, window_id: int) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Check the health of a context window.

        Args:
            window_id: Context window ID

        Returns:
            Tuple[bool, str, Dict[str, Any]]: (is_healthy, message, details)
        """
        try:
            # Get window from database
            window = self.session.get(ContextWindow, window_id)
            if not window:
                return False, f"Window {window_id} not found", {}

            # Check token usage
            token_usage_percent = (window.current_tokens / window.max_tokens) * 100 if window.max_tokens > 0 else 0
            details = {
                "window_id": window_id,
                "max_tokens": window.max_tokens,
                "current_tokens": window.current_tokens,
                "token_usage_percent": token_usage_percent
            }

            # Determine health status
            if token_usage_percent > 90:
                return False, f"Critical token usage: {token_usage_percent:.2f}%", details
            elif token_usage_percent > 75:
                return False, f"High token usage: {token_usage_percent:.2f}%", details
            else:
                return True, f"Healthy token usage: {token_usage_percent:.2f}%", details
        except Exception as e:
            logger.error(f"Error checking window health: {str(e)}")
            return False, f"Error checking window health: {str(e)}", {}


class ContextWindowMonitor:
    """
    Monitor for context window usage.
    """

    def __init__(self, session: Optional[Session] = None, cache: Optional[RedisCache] = None):
        """
        Initialize context window monitor.

        Args:
            session: SQLAlchemy session
            cache: Redis cache
        """
        self.session = session or DatabaseConnectionFactory.get_session()
        self.cache = cache or RedisCache(prefix="context_monitor")
        self.metrics = ContextWindowMetrics(self.session, self.cache)

    def monitor_window(self, window_id: int) -> Dict[str, Any]:
        """
        Monitor a context window and return its status.

        Args:
            window_id: Context window ID

        Returns:
            Dict[str, Any]: Window status
        """
        try:
            # Get window from database
            window = self.session.get(ContextWindow, window_id)
            if not window:
                return {"error": f"Window {window_id} not found"}

            # Check window health
            is_healthy, message, details = self.metrics.get_window_health(window_id)

            # Get window metrics
            metrics = self.metrics.get_window_metrics(window_id)

            # Compile status
            return {
                "window_id": window_id,
                "is_healthy": is_healthy,
                "message": message,
                "details": details,
                "metrics": metrics
            }
        except Exception as e:
            logger.error(f"Error monitoring window: {str(e)}")
            return {"error": str(e)}

    def get_windows_requiring_pruning(self, threshold_percent: float = 75.0) -> List[int]:
        """
        Get a list of context windows that require pruning.

        Args:
            threshold_percent: Token usage threshold percentage

        Returns:
            List[int]: List of window IDs requiring pruning
        """
        try:
            # Query for windows with high token usage
            query = (
                select(ContextWindow.id)
                .where(
                    ContextWindow.is_active == True,
                    ContextWindow.current_tokens >= ContextWindow.max_tokens * (threshold_percent / 100)
                )
            )
            result = self.session.execute(query)
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error getting windows requiring pruning: {str(e)}")
            return []

    def record_pruning_result(
        self,
        window_id: int,
        strategy_name: str,
        tokens_before: int,
        tokens_after: int,
        items_removed: int
    ) -> None:
        """
        Record the result of a pruning operation.

        Args:
            window_id: Context window ID
            strategy_name: Name of the pruning strategy used
            tokens_before: Number of tokens before pruning
            tokens_after: Number of tokens after pruning
            items_removed: Number of items removed
        """
        self.metrics.record_pruning_event(
            window_id=window_id,
            strategy_name=strategy_name,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            items_removed=items_removed
        )

    def get_global_status(self) -> Dict[str, Any]:
        """
        Get global context window status.

        Returns:
            Dict[str, Any]: Global status
        """
        try:
            # Get global metrics
            metrics = self.metrics.get_global_metrics()

            # Get windows requiring pruning
            windows_requiring_pruning = self.get_windows_requiring_pruning()

            # Compile status
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": metrics,
                "windows_requiring_pruning": windows_requiring_pruning,
                "windows_requiring_pruning_count": len(windows_requiring_pruning)
            }
        except Exception as e:
            logger.error(f"Error getting global status: {str(e)}")
            return {"error": str(e)}
