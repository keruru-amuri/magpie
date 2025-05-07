"""
Unit tests for logging module.
"""

import logging
import os
from unittest.mock import MagicMock, patch

import pytest
from loguru import logger

from app.core.logging import (
    InterceptHandler,
    get_logger,
    initialize_logging,
    intercept_standard_logging,
    set_log_extras,
    setup_logging,
)


@pytest.fixture
def mock_record():
    """Create a mock log record."""
    record = {"extra": {}}
    return record


def test_set_log_extras(mock_record):
    """Test that set_log_extras adds expected fields to the record."""
    # Call function
    set_log_extras(mock_record)

    # Check that expected fields were added
    assert "timestamp" in mock_record["extra"]
    assert "host" in mock_record["extra"]
    assert "pid" in mock_record["extra"]
    assert "app_name" in mock_record["extra"]

    # Check that pid is correct
    assert mock_record["extra"]["pid"] == os.getpid()


def test_get_logger():
    """Test that get_logger returns a bound logger."""
    # Mock logger.bind
    with patch("app.core.logging.logger") as mock_logger:
        mock_bound_logger = MagicMock()
        mock_logger.bind.return_value = mock_bound_logger

        # Call function
        get_logger("test_module")

        # Check that logger.bind was called with the correct name
        mock_logger.bind.assert_called_once_with(name="test_module")


@patch("app.core.logging.logger")
def test_setup_logging(mock_logger):
    """Test that setup_logging configures loguru correctly."""
    # Call function
    setup_logging(console_logging=True, file_logging=False)

    # Check that logger.remove was called
    mock_logger.remove.assert_called_once()

    # Check that logger.add was called for console
    mock_logger.add.assert_called_once()


@patch("app.core.logging.logging")
def test_intercept_standard_logging(mock_logging):
    """Test that intercept_standard_logging configures standard logging correctly."""
    # Mock loggerDict
    mock_logging.root.manager.loggerDict = {
        "uvicorn": MagicMock(),
        "fastapi": MagicMock(),
        "other": MagicMock(),
    }

    # Mock getLogger
    mock_logging.getLogger.return_value = MagicMock()

    # Call function
    intercept_standard_logging()

    # Check that basicConfig was called
    mock_logging.basicConfig.assert_called_once()

    # Check that getLogger was called at least once for each logger in loggerDict
    assert mock_logging.getLogger.call_count >= len(mock_logging.root.manager.loggerDict)


def test_intercept_handler():
    """Test that InterceptHandler correctly intercepts standard logging messages."""
    # Create a standard logging record
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    # Create handler
    handler = InterceptHandler()

    # Mock logger.opt
    with patch("app.core.logging.logger") as mock_logger:
        mock_opt = MagicMock()
        mock_level = MagicMock()
        mock_level.name = "INFO"
        mock_logger.level.return_value = mock_level
        mock_logger.opt.return_value = mock_opt

        # Call handler
        handler.emit(record)

        # Check that logger.opt was called
        mock_logger.opt.assert_called_once()

        # Check that log was called with the correct message
        mock_opt.log.assert_called_once()
        args, _ = mock_opt.log.call_args
        assert args[1] == "Test message"
