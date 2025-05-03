"""Integration tests for health endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from tests.integration.base import BaseAPIIntegrationTest


class TestHealthEndpoints(BaseAPIIntegrationTest):
    """Tests for health endpoints."""

    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Welcome to MAGPIE - MAG Platform for Intelligent Execution"
        assert data["version"] == settings.VERSION
        assert data["status"] == "operational"
        assert data["documentation"] == "/docs"
        assert data["api_version"] == settings.API_V1_STR

    def test_health_endpoint(self):
        """Test the health endpoint."""
        response = self.client.get(f"{settings.API_V1_STR}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["environment"] == settings.ENVIRONMENT
        assert "debug" in data
        assert data["version"] == settings.VERSION

    def test_detailed_health_endpoint(self):
        """Test the detailed health endpoint."""
        response = self.client.get(f"{settings.API_V1_STR}/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "api" in data
        assert "database" in data
        assert "redis" in data
        assert "azure_openai" in data
        assert data["api"]["version"] == settings.VERSION
        assert data["api"]["environment"] == settings.ENVIRONMENT


@pytest.mark.parametrize(
    "endpoint,expected_content_type",
    [
        ("/docs", "text/html"),
        ("/redoc", "text/html"),
        (f"{settings.API_V1_STR}/openapi.json", "application/json"),
    ],
)
def test_documentation_endpoints(endpoint, expected_content_type):
    """Test the documentation endpoints."""
    client = TestClient(app)
    response = client.get(endpoint)
    assert response.status_code == 200
    assert expected_content_type in response.headers["content-type"]
