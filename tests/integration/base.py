"""Base test classes for integration tests."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.api.deps import get_db
from app.main import app
from tests.db_utils import test_session, override_get_db


class BaseIntegrationTest:
    """Base test class for all integration tests."""

    @pytest.fixture(autouse=True)
    def setup(self, test_session):
        """Set up test environment."""
        self.app = app
        self.db = test_session

        # Add any common setup here
        yield
        # Add any common teardown here


class BaseAPIIntegrationTest(BaseIntegrationTest):
    """Base test class for API integration tests."""

    @pytest.fixture(autouse=True)
    def setup_api(self, override_get_db):
        """Set up API test environment."""
        # Override the get_db dependency
        self.app.dependency_overrides[get_db] = override_get_db

        # Create a test client
        self.client = TestClient(self.app)

        yield

        # Clean up
        self.app.dependency_overrides.clear()


class BaseAsyncAPIIntegrationTest(BaseAPIIntegrationTest):
    """Base test class for async API integration tests."""

    @pytest.fixture
    async def async_client(self):
        """Create an async test client for the FastAPI application."""
        async with AsyncClient(app=self.app, base_url="http://test") as test_client:
            yield test_client
