"""
Database utilities for testing.

This module provides utilities for setting up and tearing down test databases.
"""
import asyncio
import contextlib
from typing import AsyncGenerator, Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db.connection import Base


def get_test_db_engine(db_url="sqlite:///:memory:"):
    """
    Create a SQLAlchemy engine for testing.

    Args:
        db_url: Database URL (default: in-memory SQLite)

    Returns:
        Engine: SQLAlchemy engine
    """
    # Use in-memory SQLite database for testing with thread-local connections
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    # Create tables
    Base.metadata.create_all(engine)

    return engine


def get_test_db_session_factory(engine):
    """
    Create a SQLAlchemy session factory for testing.

    Args:
        engine: SQLAlchemy engine

    Returns:
        sessionmaker: SQLAlchemy session factory
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextlib.contextmanager
def get_test_db_session(engine) -> Generator[Session, None, None]:
    """
    Get a database session as a context manager.

    Args:
        engine: SQLAlchemy engine

    Yields:
        Session: SQLAlchemy session
    """
    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="module")
def test_engine():
    """
    Create SQLAlchemy engine for testing.

    Yields:
        Engine: SQLAlchemy engine
    """
    engine = get_test_db_engine()

    yield engine

    # Drop tables
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_session(test_engine):
    """
    Create SQLAlchemy session for testing.

    Args:
        test_engine: SQLAlchemy engine

    Yields:
        Session: SQLAlchemy session
    """
    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Create a transaction
    connection = test_engine.connect()
    transaction = connection.begin()

    # Create session
    session = TestingSessionLocal(bind=connection)

    yield session

    # Rollback the transaction and close the connection
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def override_get_db(test_session):
    """
    Override the get_db dependency.

    Args:
        test_session: SQLAlchemy session

    Yields:
        Session: SQLAlchemy session
    """
    def _get_test_db():
        try:
            yield test_session
        finally:
            pass

    return _get_test_db


# Async database utilities
def get_async_test_db_engine(db_url="sqlite+aiosqlite:///:memory:"):
    """
    Create an async SQLAlchemy engine for testing.

    Args:
        db_url: Database URL (default: in-memory SQLite)

    Returns:
        AsyncEngine: SQLAlchemy async engine
    """
    # Use in-memory SQLite database for testing with thread-local connections
    engine = create_async_engine(
        db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    return engine


async def create_async_tables(engine):
    """
    Create tables in the async database.

    Args:
        engine: SQLAlchemy async engine
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_async_tables(engine):
    """
    Drop tables in the async database.

    Args:
        engine: SQLAlchemy async engine
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="module")
async def async_test_engine():
    """
    Create async SQLAlchemy engine for testing.

    Yields:
        AsyncEngine: SQLAlchemy async engine
    """
    engine = get_async_test_db_engine()

    await create_async_tables(engine)

    yield engine

    await drop_async_tables(engine)


@pytest.fixture(scope="function")
async def async_test_session(async_test_engine):
    """
    Create async SQLAlchemy session for testing.

    Args:
        async_test_engine: SQLAlchemy async engine

    Yields:
        AsyncSession: SQLAlchemy async session
    """
    # Create async session factory
    async_session = sessionmaker(
        bind=async_test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        async with async_test_engine.begin() as conn:
            # Start a nested transaction
            await session.begin_nested()

            # Yield the session
            yield session

            # Rollback the transaction
            await session.rollback()


@pytest.fixture(scope="function")
async def async_override_get_db(async_test_session):
    """
    Override the get_db dependency for async operations.

    Args:
        async_test_session: SQLAlchemy async session

    Yields:
        AsyncSession: SQLAlchemy async session
    """
    async def _get_async_test_db():
        try:
            yield async_test_session
        finally:
            pass

    return _get_async_test_db
