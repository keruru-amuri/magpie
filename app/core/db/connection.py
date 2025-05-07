"""
Database connection module for the MAGPIE platform.
"""
import contextlib
import logging
import os
from typing import Any, Dict, Generator, Optional

from sqlalchemy import create_engine, event, exc, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool, NullPool

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Determine if we're in testing mode
TESTING = os.environ.get("TESTING", "").lower() in ("true", "1", "t")

# Create SQLAlchemy engine with appropriate configuration
if TESTING:
    # Use in-memory SQLite for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
        echo=settings.DB_ECHO,
    )
else:
    # Use PostgreSQL for production/development
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,
        poolclass=QueuePool,
        echo=settings.DB_ECHO,
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Set SQLite pragma for foreign key support.
    Only applies to SQLite connections.
    """
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    """
    Get a database session.

    Yields:
        Session: SQLAlchemy session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextlib.contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Get a database session as a context manager.

    Yields:
        Session: SQLAlchemy session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseConnectionFactory:
    """
    Factory class for managing database connections.
    """

    @staticmethod
    def get_session() -> Session:
        """
        Get a new database session.

        Returns:
            Session: SQLAlchemy session
        """
        return SessionLocal()

    @staticmethod
    def get_engine() -> Engine:
        """
        Get the SQLAlchemy engine.

        Returns:
            Engine: SQLAlchemy engine
        """
        return engine

    @staticmethod
    @contextlib.contextmanager
    def session_context() -> Generator[Session, None, None]:
        """
        Get a database session as a context manager.

        Yields:
            Session: SQLAlchemy session
        """
        session = SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Session rolled back due to exception: {str(e)}")
            raise
        finally:
            session.close()

    @staticmethod
    def execute_query(query: str, params: Dict[str, Any] = None) -> Any:
        """
        Execute a raw SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Any: Query result
        """
        with DatabaseConnectionFactory.session_context() as session:
            try:
                # Convert string query to text object
                if isinstance(query, str):
                    query = text(query)

                result = session.execute(query, params or {})
                return result
            except exc.SQLAlchemyError as e:
                logger.error(f"Error executing query: {str(e)}")
                raise
