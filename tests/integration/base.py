"""Base test classes for integration tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class BaseIntegrationTest:
    """Base test class for all integration tests."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.app = app
        self.client = TestClient(self.app)
        
        # Add any common setup here
        yield
        # Add any common teardown here


class BaseAPIIntegrationTest(BaseIntegrationTest):
    """Base test class for API integration tests."""

    @pytest.fixture(autouse=True)
    def setup_api(self):
        """Set up API test environment."""
        # Add API-specific setup here
        yield
        # Add API-specific teardown here
