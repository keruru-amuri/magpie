"""Pytest configuration for MAGPIE platform."""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config import settings
from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI application."""
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client


@pytest.fixture(scope="session")
def test_environment():
    """Set up test environment variables."""
    # Store original environment
    original_env = os.environ.copy()

    # Set test environment variables
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DEBUG"] = "true"

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="function")
def override_settings():
    """Override settings for testing."""
    original_settings = {
        "ENVIRONMENT": settings.ENVIRONMENT,
        "DEBUG": settings.DEBUG,
        "PROJECT_NAME": settings.PROJECT_NAME,
    }

    # Override settings for testing
    settings.ENVIRONMENT = "testing"
    settings.DEBUG = True
    settings.PROJECT_NAME = "MAGPIE-Test"

    yield settings

    # Restore original settings
    settings.ENVIRONMENT = original_settings["ENVIRONMENT"]
    settings.DEBUG = original_settings["DEBUG"]
    settings.PROJECT_NAME = original_settings["PROJECT_NAME"]


@pytest.fixture(scope="function")
def mock_azure_openai(monkeypatch):
    """Mock Azure OpenAI API calls."""
    class MockAzureOpenAI:
        def __init__(self, *args, **kwargs):
            pass

        def chat_completions(self, *args, **kwargs):
            return {
                "choices": [
                    {
                        "message": {
                            "content": "This is a mock response from Azure OpenAI."
                        }
                    }
                ]
            }

    monkeypatch.setattr("app.services.azure_openai.AzureOpenAI", MockAzureOpenAI)
    return MockAzureOpenAI
