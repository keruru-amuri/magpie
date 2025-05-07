"""
Unit tests for database health check.
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.health import DatabaseHealthCheck


class TestDatabaseHealthCheck:
    """
    Test database health check functionality.
    """
    
    def test_check_connection_success(self):
        """
        Test check_connection method with successful connection.
        """
        # Check connection
        is_healthy, message = DatabaseHealthCheck.check_connection()
        
        # Verify connection is healthy
        assert is_healthy is True
        assert "healthy" in message
    
    @patch('app.core.db.health.DatabaseConnectionFactory.session_context')
    def test_check_connection_failure(self, mock_session_context):
        """
        Test check_connection method with failed connection.
        """
        # Mock session context to raise exception
        mock_context = MagicMock()
        mock_context.__enter__.side_effect = SQLAlchemyError("Connection error")
        mock_session_context.return_value = mock_context
        
        # Check connection
        is_healthy, message = DatabaseHealthCheck.check_connection()
        
        # Verify connection is not healthy
        assert is_healthy is False
        assert "error" in message.lower()
    
    def test_get_database_info(self):
        """
        Test get_database_info method.
        """
        # Get database info
        info = DatabaseHealthCheck.get_database_info()
        
        # Verify info is returned
        assert isinstance(info, dict)
        
        # Check for expected keys in SQLite info
        if "driver" in info:
            assert "status" in info
            assert info["status"] == "connected"
        # Check for expected keys in PostgreSQL info
        elif "version" in info:
            assert "size" in info
            assert "active_connections" in info
    
    @patch('app.core.db.health.DatabaseConnectionFactory.session_context')
    def test_get_database_info_error(self, mock_session_context):
        """
        Test get_database_info method with error.
        """
        # Mock session context to raise exception
        mock_context = MagicMock()
        mock_context.__enter__.side_effect = SQLAlchemyError("Database error")
        mock_session_context.return_value = mock_context
        
        # Get database info
        info = DatabaseHealthCheck.get_database_info()
        
        # Verify error is returned
        assert "error" in info
    
    @patch('app.core.db.health.DatabaseConnectionFactory.session_context')
    def test_check_migrations_table_exists(self, mock_session_context):
        """
        Test check_migrations method when alembic_version table exists.
        """
        # Mock session and query execution
        mock_session = MagicMock()
        mock_session.execute.side_effect = [
            MagicMock(scalar=lambda: True),  # Table exists
            MagicMock(scalar=lambda: "1234abcd")  # Version
        ]
        
        # Mock context manager
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_session
        mock_session_context.return_value = mock_context
        
        # Check migrations
        is_up_to_date, message = DatabaseHealthCheck.check_migrations()
        
        # Verify migrations are up to date
        assert is_up_to_date is True
        assert "up to date" in message
        assert "1234abcd" in message
    
    @patch('app.core.db.health.DatabaseConnectionFactory.session_context')
    def test_check_migrations_table_not_exists(self, mock_session_context):
        """
        Test check_migrations method when alembic_version table does not exist.
        """
        # Mock session and query execution
        mock_session = MagicMock()
        mock_session.execute.return_value = MagicMock(scalar=lambda: False)
        
        # Mock context manager
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_session
        mock_session_context.return_value = mock_context
        
        # Check migrations
        is_up_to_date, message = DatabaseHealthCheck.check_migrations()
        
        # Verify migrations are not up to date
        assert is_up_to_date is False
        assert "not been initialized" in message
    
    @patch('app.core.db.health.DatabaseConnectionFactory.session_context')
    def test_check_migrations_no_version(self, mock_session_context):
        """
        Test check_migrations method when no version is found.
        """
        # Mock session and query execution
        mock_session = MagicMock()
        mock_session.execute.side_effect = [
            MagicMock(scalar=lambda: True),  # Table exists
            MagicMock(scalar=lambda: None)   # No version
        ]
        
        # Mock context manager
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_session
        mock_session_context.return_value = mock_context
        
        # Check migrations
        is_up_to_date, message = DatabaseHealthCheck.check_migrations()
        
        # Verify migrations are not up to date
        assert is_up_to_date is False
        assert "No migrations" in message
    
    @patch('app.core.db.health.DatabaseConnectionFactory.session_context')
    def test_check_migrations_error(self, mock_session_context):
        """
        Test check_migrations method with error.
        """
        # Mock session context to raise exception
        mock_context = MagicMock()
        mock_context.__enter__.side_effect = SQLAlchemyError("Migration error")
        mock_session_context.return_value = mock_context
        
        # Check migrations
        is_up_to_date, message = DatabaseHealthCheck.check_migrations()
        
        # Verify error is returned
        assert is_up_to_date is False
        assert "error" in message.lower()
