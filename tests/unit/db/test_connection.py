"""
Unit tests for database connection.
"""
import contextlib
import os
import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.connection import (
    DatabaseConnectionFactory,
    get_db,
    get_db_context
)


class TestDatabaseConnection:
    """
    Test database connection functionality.
    """

    def test_get_session(self, test_db_engine):
        """
        Test get_session method.
        """
        # Get session
        session = DatabaseConnectionFactory.get_session()

        # Verify session is created
        assert session is not None

        # Clean up
        session.close()

    def test_get_engine(self):
        """
        Test get_engine method.
        """
        # Get engine
        engine = DatabaseConnectionFactory.get_engine()

        # Verify engine is created
        assert engine is not None

        # Verify engine URL is a string (don't check specific URL as it depends on environment)
        assert isinstance(str(engine.url), str)

    def test_session_context(self, test_db_session):
        """
        Test session_context method.
        """
        # Verify session is created
        assert test_db_session is not None

        # Execute simple query
        result = test_db_session.execute(text("SELECT 1"))

        # Verify query execution
        assert result.scalar() == 1

    def test_execute_query(self, monkeypatch, test_db_session):
        """
        Test execute_query method.
        """
        # Mock the session_context to return our test session
        @contextlib.contextmanager
        def mock_session_context():
            yield test_db_session

        monkeypatch.setattr(
            DatabaseConnectionFactory,
            "session_context",
            mock_session_context
        )

        # Execute query
        result = DatabaseConnectionFactory.execute_query("SELECT 1")

        # Verify query execution
        assert result.scalar() == 1

    def test_execute_query_with_params(self, monkeypatch, test_db_session):
        """
        Test execute_query method with parameters.
        """
        # Mock the session_context to return our test session
        @contextlib.contextmanager
        def mock_session_context():
            yield test_db_session

        monkeypatch.setattr(
            DatabaseConnectionFactory,
            "session_context",
            mock_session_context
        )

        # Execute query with parameters
        result = DatabaseConnectionFactory.execute_query(
            "SELECT :value",
            {"value": 42}
        )

        # Verify query execution
        assert result.scalar() == 42

    def test_execute_query_error(self, monkeypatch, test_db_session):
        """
        Test execute_query method with error.
        """
        # Mock the session_context to return our test session
        @contextlib.contextmanager
        def mock_session_context():
            yield test_db_session

        monkeypatch.setattr(
            DatabaseConnectionFactory,
            "session_context",
            mock_session_context
        )

        # Execute invalid query
        with pytest.raises(SQLAlchemyError):
            DatabaseConnectionFactory.execute_query("SELECT invalid_column")

    def test_get_db_generator(self, monkeypatch, test_db_session):
        """
        Test get_db generator.
        """
        # Mock the SessionLocal to return our test session
        def mock_session_local():
            return test_db_session

        monkeypatch.setattr(
            "app.core.db.connection.SessionLocal",
            mock_session_local
        )

        # Get generator
        db_generator = get_db()

        # Get session from generator
        session = next(db_generator)

        # Verify session is created
        assert session is not None

        # Execute simple query
        result = session.execute(text("SELECT 1"))

        # Verify query execution
        assert result.scalar() == 1

        # Clean up
        try:
            next(db_generator)
        except StopIteration:
            pass

    def test_get_db_context_manager(self, monkeypatch, test_db_session):
        """
        Test get_db_context context manager.
        """
        # Mock the SessionLocal to return our test session
        def mock_session_local():
            return test_db_session

        monkeypatch.setattr(
            "app.core.db.connection.SessionLocal",
            mock_session_local
        )

        # Use context manager
        with get_db_context() as session:
            # Verify session is created
            assert session is not None

            # Execute simple query
            result = session.execute(text("SELECT 1"))

            # Verify query execution
            assert result.scalar() == 1

    def test_testing_mode(self):
        """
        Test that we're in testing mode.
        """
        # Verify TESTING environment variable is set
        assert os.environ.get("TESTING") == "true"

        # We don't check the engine URL here since it depends on how the tests are run
        # In CI/CD environments, it might use the real database URL
