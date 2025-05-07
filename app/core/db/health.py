"""
Database health check module for the MAGPIE platform.
"""
import logging
from typing import Dict, Tuple

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.connection import DatabaseConnectionFactory

# Configure logging
logger = logging.getLogger(__name__)


class DatabaseHealthCheck:
    """
    Health check functionality for the database.
    """
    
    @staticmethod
    def check_connection() -> Tuple[bool, str]:
        """
        Check if the database connection is healthy.
        
        Returns:
            Tuple[bool, str]: (is_healthy, message)
        """
        try:
            with DatabaseConnectionFactory.session_context() as session:
                # Execute a simple query to check connection
                session.execute(text("SELECT 1"))
            return True, "Database connection is healthy"
        except SQLAlchemyError as e:
            error_message = f"Database connection error: {str(e)}"
            logger.error(error_message)
            return False, error_message
    
    @staticmethod
    def get_database_info() -> Dict[str, str]:
        """
        Get information about the database.
        
        Returns:
            Dict[str, str]: Database information
        """
        try:
            with DatabaseConnectionFactory.session_context() as session:
                if "postgresql" in DatabaseConnectionFactory.get_engine().url.drivername:
                    # PostgreSQL specific queries
                    version_query = text("SELECT version()")
                    version = session.execute(version_query).scalar()
                    
                    size_query = text("""
                        SELECT pg_size_pretty(pg_database_size(current_database()))
                    """)
                    size = session.execute(size_query).scalar()
                    
                    connections_query = text("""
                        SELECT count(*) FROM pg_stat_activity 
                        WHERE datname = current_database()
                    """)
                    connections = session.execute(connections_query).scalar()
                    
                    return {
                        "version": version,
                        "size": size,
                        "active_connections": str(connections),
                    }
                else:
                    # Generic info for other database types
                    return {
                        "status": "connected",
                        "driver": DatabaseConnectionFactory.get_engine().url.drivername,
                    }
        except SQLAlchemyError as e:
            logger.error(f"Error getting database info: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def check_migrations() -> Tuple[bool, str]:
        """
        Check if all migrations have been applied.
        
        Returns:
            Tuple[bool, str]: (is_up_to_date, message)
        """
        try:
            with DatabaseConnectionFactory.session_context() as session:
                # Check if alembic_version table exists
                check_table_query = text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'alembic_version'
                    )
                """)
                table_exists = session.execute(check_table_query).scalar()
                
                if not table_exists:
                    return False, "Migrations have not been initialized"
                
                # Check if there are any migrations in the table
                version_query = text("SELECT version_num FROM alembic_version")
                version = session.execute(version_query).scalar()
                
                if not version:
                    return False, "No migrations have been applied"
                
                return True, f"Migrations are up to date (current: {version})"
        except SQLAlchemyError as e:
            error_message = f"Error checking migrations: {str(e)}"
            logger.error(error_message)
            return False, error_message
