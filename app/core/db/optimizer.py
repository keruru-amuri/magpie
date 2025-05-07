"""
Database query optimizer for the MAGPIE platform.

This module provides functionality for optimizing database queries
to improve performance and reduce database load.
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union, cast

from sqlalchemy import Column, Table, func, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql import Select

from app.core.config import settings
from app.core.db.connection import DatabaseConnectionFactory
from app.core.monitoring.profiling import profile_function, PerformanceCategory

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for function return type
F = TypeVar('F', bound=Callable[..., Any])


class QueryOptimizer:
    """
    Optimizer for database queries.
    """
    
    def __init__(
        self,
        enabled: bool = True,
        slow_query_threshold_ms: int = 100,
    ):
        """
        Initialize query optimizer.
        
        Args:
            enabled: Whether optimization is enabled
            slow_query_threshold_ms: Threshold for slow queries in milliseconds
        """
        self.enabled = enabled
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.logger = logger
        
        # Set of tables with missing indexes
        self.tables_missing_indexes: Set[str] = set()
        
        # Dictionary of slow queries
        self.slow_queries: Dict[str, Dict[str, Any]] = {}
    
    def analyze_query(self, query: Union[Query, Select, str], duration_ms: float) -> Dict[str, Any]:
        """
        Analyze a query for performance issues.
        
        Args:
            query: SQLAlchemy query or SQL string
            duration_ms: Query duration in milliseconds
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        if not self.enabled:
            return {"enabled": False}
        
        # Convert query to string
        if isinstance(query, str):
            query_str = query
        elif hasattr(query, 'statement'):
            query_str = str(query.statement.compile(
                compile_kwargs={"literal_binds": True}
            ))
        else:
            query_str = str(query.compile(
                compile_kwargs={"literal_binds": True}
            ))
        
        # Check if query is slow
        is_slow = duration_ms > self.slow_query_threshold_ms
        
        # Extract tables from query
        tables = []
        if not isinstance(query, str):
            if hasattr(query, 'statement'):
                statement = query.statement
            else:
                statement = query
            
            for table in statement.froms:
                if isinstance(table, Table):
                    tables.append(table.name)
        
        # Create analysis results
        analysis = {
            "query": query_str[:200] + "..." if len(query_str) > 200 else query_str,
            "duration_ms": duration_ms,
            "is_slow": is_slow,
            "tables": tables,
            "timestamp": time.time(),
        }
        
        # Add to slow queries if slow
        if is_slow:
            query_hash = hash(query_str)
            self.slow_queries[str(query_hash)] = analysis
            
            # Log slow query
            self.logger.warning(
                f"Slow query detected: {duration_ms:.2f}ms",
                extra={
                    "query": query_str[:200] + "..." if len(query_str) > 200 else query_str,
                    "duration_ms": duration_ms,
                    "tables": tables,
                }
            )
        
        return analysis
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get slow queries.
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List[Dict[str, Any]]: List of slow queries
        """
        if not self.enabled:
            return []
        
        # Sort slow queries by duration (descending)
        sorted_queries = sorted(
            self.slow_queries.values(),
            key=lambda q: q["duration_ms"],
            reverse=True
        )
        
        # Return top N
        return sorted_queries[:limit]
    
    def clear_slow_queries(self) -> None:
        """
        Clear slow queries.
        """
        self.slow_queries.clear()
    
    def check_missing_indexes(self, session: Session) -> Dict[str, List[str]]:
        """
        Check for missing indexes in the database.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            Dict[str, List[str]]: Dictionary of tables and columns missing indexes
        """
        if not self.enabled:
            return {}
        
        # Only supported for PostgreSQL
        if not settings.DATABASE_URL.startswith("postgresql"):
            return {}
        
        try:
            # Query for missing indexes
            query = text("""
                SELECT
                    schemaname,
                    relname AS table_name,
                    seq_scan,
                    idx_scan,
                    seq_scan - idx_scan AS diff,
                    n_live_tup AS rows
                FROM
                    pg_stat_user_tables
                WHERE
                    seq_scan > idx_scan
                    AND n_live_tup > 1000
                ORDER BY
                    diff DESC,
                    rows DESC;
            """)
            
            result = session.execute(query)
            
            # Process results
            missing_indexes = {}
            for row in result:
                table_name = row.table_name
                
                # Add table to missing indexes
                if table_name not in missing_indexes:
                    missing_indexes[table_name] = []
                
                # Add table to tables missing indexes
                self.tables_missing_indexes.add(table_name)
            
            # For each table, check which columns might need indexes
            for table_name in self.tables_missing_indexes:
                # Query for columns that might need indexes
                query = text(f"""
                    SELECT
                        a.attname AS column_name
                    FROM
                        pg_stat_user_tables t
                        JOIN pg_attribute a ON a.attrelid = t.relid
                    WHERE
                        t.relname = :table_name
                        AND a.attnum > 0
                        AND NOT a.attisdropped
                        AND a.atttypid IN (
                            23,  -- int4
                            21,  -- int2
                            20,  -- int8
                            1043,  -- varchar
                            25,  -- text
                            1082,  -- date
                            1114,  -- timestamp
                            1184  -- timestamptz
                        )
                    ORDER BY
                        a.attnum;
                """)
                
                result = session.execute(query, {"table_name": table_name})
                
                # Add columns to missing indexes
                for row in result:
                    missing_indexes[table_name].append(row.column_name)
            
            return missing_indexes
        except Exception as e:
            self.logger.error(f"Error checking missing indexes: {str(e)}")
            return {}
    
    def get_table_statistics(self, session: Session) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for tables in the database.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of table statistics
        """
        if not self.enabled:
            return {}
        
        # Only supported for PostgreSQL
        if not settings.DATABASE_URL.startswith("postgresql"):
            return {}
        
        try:
            # Query for table statistics
            query = text("""
                SELECT
                    relname AS table_name,
                    n_live_tup AS row_count,
                    n_dead_tup AS dead_rows,
                    last_vacuum,
                    last_analyze
                FROM
                    pg_stat_user_tables
                ORDER BY
                    n_live_tup DESC;
            """)
            
            result = session.execute(query)
            
            # Process results
            table_stats = {}
            for row in result:
                table_name = row.table_name
                
                # Add table to table statistics
                table_stats[table_name] = {
                    "row_count": row.row_count,
                    "dead_rows": row.dead_rows,
                    "last_vacuum": row.last_vacuum,
                    "last_analyze": row.last_analyze,
                }
            
            return table_stats
        except Exception as e:
            self.logger.error(f"Error getting table statistics: {str(e)}")
            return {}
    
    def get_index_usage(self, session: Session) -> Dict[str, Dict[str, Any]]:
        """
        Get index usage statistics.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of index usage statistics
        """
        if not self.enabled:
            return {}
        
        # Only supported for PostgreSQL
        if not settings.DATABASE_URL.startswith("postgresql"):
            return {}
        
        try:
            # Query for index usage
            query = text("""
                SELECT
                    t.relname AS table_name,
                    i.relname AS index_name,
                    s.idx_scan AS index_scans,
                    pg_size_pretty(pg_relation_size(i.oid)) AS index_size,
                    a.attname AS column_name
                FROM
                    pg_stat_user_indexes s
                    JOIN pg_class t ON t.oid = s.relid
                    JOIN pg_class i ON i.oid = s.indexrelid
                    JOIN pg_index ix ON ix.indexrelid = s.indexrelid
                    JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                ORDER BY
                    t.relname,
                    i.relname;
            """)
            
            result = session.execute(query)
            
            # Process results
            index_usage = {}
            for row in result:
                table_name = row.table_name
                index_name = row.index_name
                
                # Add table to index usage
                if table_name not in index_usage:
                    index_usage[table_name] = {}
                
                # Add index to table
                if index_name not in index_usage[table_name]:
                    index_usage[table_name][index_name] = {
                        "index_scans": row.index_scans,
                        "index_size": row.index_size,
                        "columns": [],
                    }
                
                # Add column to index
                index_usage[table_name][index_name]["columns"].append(row.column_name)
            
            return index_usage
        except Exception as e:
            self.logger.error(f"Error getting index usage: {str(e)}")
            return {}
    
    def get_optimization_recommendations(self, session: Session) -> Dict[str, Any]:
        """
        Get optimization recommendations.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            Dict[str, Any]: Optimization recommendations
        """
        if not self.enabled:
            return {"enabled": False}
        
        # Get missing indexes
        missing_indexes = self.check_missing_indexes(session)
        
        # Get table statistics
        table_stats = self.get_table_statistics(session)
        
        # Get index usage
        index_usage = self.get_index_usage(session)
        
        # Get slow queries
        slow_queries = self.get_slow_queries()
        
        # Create recommendations
        recommendations = {
            "enabled": True,
            "missing_indexes": missing_indexes,
            "table_stats": table_stats,
            "index_usage": index_usage,
            "slow_queries": slow_queries,
            "timestamp": time.time(),
        }
        
        return recommendations


# Create a global query optimizer instance
query_optimizer = QueryOptimizer(
    enabled=settings.ENVIRONMENT != "testing",
)


@profile_function(PerformanceCategory.DATABASE)
def optimized_query(func: F) -> F:
    """
    Decorator for optimizing and analyzing queries.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Skip optimization if disabled
        if not query_optimizer.enabled:
            return func(*args, **kwargs)
        
        # Record start time
        start_time = time.time()
        
        try:
            # Call original function
            result = func(*args, **kwargs)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Analyze query
            if hasattr(result, 'statement'):
                # Result is a SQLAlchemy Query object
                query_optimizer.analyze_query(result, duration_ms)
            
            return result
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                f"Error executing query: {str(e)}",
                extra={
                    "duration_ms": duration_ms,
                    "function": func.__name__,
                }
            )
            
            # Re-raise exception
            raise
    
    return cast(F, wrapper)
