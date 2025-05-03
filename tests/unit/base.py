"""Base test classes for unit tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class BaseTest:
    """Base test class for all unit tests."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.app = app
        self.client = TestClient(self.app)
        
        # Add any common setup here
        yield
        # Add any common teardown here


class BaseAPITest(BaseTest):
    """Base test class for API tests."""

    @pytest.fixture(autouse=True)
    def setup_api(self):
        """Set up API test environment."""
        # Add API-specific setup here
        yield
        # Add API-specific teardown here


class BaseAsyncTest(BaseTest):
    """Base test class for async tests."""

    @pytest.fixture(autouse=True)
    async def setup_async(self):
        """Set up async test environment."""
        # Add async-specific setup here
        yield
        # Add async-specific teardown here
