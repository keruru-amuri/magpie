"""
Logging configuration for the MAGPIE platform.

This module provides a centralized logging configuration using loguru.
It sets up structured logging with different sinks (console, file) and
configures log levels, formats, and rotation policies.
"""

import logging
import os
import sys
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional, Any

from loguru import logger

from app.core.config import settings, EnvironmentType


# Define log levels
LOG_LEVEL_MAP = {
    "debug": "DEBUG",
    "info": "INFO",
    "warning": "WARNING",
    "error": "ERROR",
    "critical": "CRITICAL",
}

# Get log level from settings
LOG_LEVEL = LOG_LEVEL_MAP.get(settings.LOG_LEVEL.lower(), "INFO")

# Define log format
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level> | "
    "{extra}"
)

# Define JSON log format for file logging
JSON_LOG_FORMAT = {
    "time": "{time:YYYY-MM-DD HH:mm:ss.SSS}",
    "level": "{level}",
    "message": "{message}",
    "name": "{name}",
    "function": "{function}",
    "line": "{line}",
    "extra": "{extra}",
}


class InterceptHandler(logging.Handler):
    """
    Intercept standard logging messages and redirect them to loguru.

    This handler intercepts all standard logging messages and redirects them
    to loguru, ensuring consistent logging format across the application.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where the logged message originated
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def set_log_extras(record: Dict[str, Any]) -> None:
    """
    Add extra contextual information to log records.

    Args:
        record: The log record to enrich with extra information
    """
    # Add timestamp in UTC
    record["extra"]["timestamp"] = datetime.now(timezone.utc)

    # Add host information
    hostname = os.getenv('HOSTNAME', os.getenv('COMPUTERNAME', 'unknown'))
    record["extra"]["host"] = hostname.split('.')[0] if hostname else 'unknown'

    # Add process ID
    record["extra"]["pid"] = os.getpid()

    # Add application name
    record["extra"]["app_name"] = settings.PROJECT_NAME


def format_record(record: Dict[str, Any]) -> str:
    """
    Custom formatter for log records.

    Args:
        record: The log record to format

    Returns:
        str: Formatted log record
    """
    # Set extra fields for the record
    set_log_extras(record)

    # Format the log message
    format_string = (
        "<green>{extra[timestamp]}</green> | "
        "<green>{extra[app_name]}</green> | "
        "<green>{extra[host]}</green> | "
        "<green>{extra[pid]}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Add exception information if present
    if record["exception"]:
        format_string += "\n{exception}"

    return format_string


def setup_logging(
    console_level: Optional[str] = None,
    file_level: Optional[str] = None,
    log_dir: Optional[str] = None,
    console_logging: bool = True,
    file_logging: bool = True,
) -> None:
    """
    Set up logging configuration.

    Args:
        console_level: Log level for console output
        file_level: Log level for file output
        log_dir: Directory to store log files
        console_logging: Whether to enable console logging
        file_logging: Whether to enable file logging
    """
    # Remove default logger
    logger.remove()

    # Use provided log levels or default from settings
    console_log_level = console_level or LOG_LEVEL
    file_log_level = file_level or LOG_LEVEL

    # Add console logger if enabled
    if console_logging:
        logger.add(
            sys.stderr,
            format=format_record,
            level=console_log_level,
            colorize=True,
            backtrace=True,
            diagnose=settings.ENVIRONMENT != EnvironmentType.PRODUCTION,  # Disable diagnose in production
        )

    # Add file logger if enabled and not in testing mode
    if file_logging and settings.ENVIRONMENT != EnvironmentType.TESTING:
        # Create log directory if it doesn't exist
        log_directory = Path(log_dir or "logs")
        log_directory.mkdir(parents=True, exist_ok=True)

        # Add file logger with rotation
        logger.add(
            log_directory / f"{settings.PROJECT_NAME.lower()}_{{time:YYYY-MM-DD}}.log",
            format="{message}",
            level=file_log_level,
            rotation="00:00",  # Rotate at midnight
            retention="30 days",  # Keep logs for 30 days
            compression="zip",  # Compress rotated logs
            serialize=True,  # Use JSON format
            backtrace=True,
            diagnose=False,  # Disable diagnose for file logs to avoid sensitive data
        )


def intercept_standard_logging() -> None:
    """
    Intercept all standard logging and redirect to loguru.

    This function configures Python's standard logging to use loguru,
    ensuring consistent log format across all libraries.
    """
    # Remove existing handlers
    for name in logging.root.manager.loggerDict.keys():
        if name.startswith("uvicorn") or name.startswith("fastapi"):
            for handler in logging.getLogger(name).handlers:
                logging.getLogger(name).removeHandler(handler)

    # Set the handler for the root logger
    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    # Update existing loggers
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = [InterceptHandler()]
        logging.getLogger(name).propagate = False


def get_logger(name: str):
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        logger: Loguru logger instance
    """
    return logger.bind(name=name)


@lru_cache()
def initialize_logging() -> None:
    """
    Initialize logging for the application.

    This function sets up loguru and intercepts standard logging.
    It is cached to ensure it's only called once.
    """
    # Set up loguru
    setup_logging(
        console_logging=True,
        file_logging=settings.ENVIRONMENT != EnvironmentType.TESTING,  # Disable file logging in testing mode
    )

    # Intercept standard logging
    intercept_standard_logging()

    # Log initialization
    logger.info(f"Logging initialized for {settings.PROJECT_NAME} in {settings.ENVIRONMENT} mode")


# Initialize logging on module import
initialize_logging()
