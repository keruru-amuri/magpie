"""Integration tests for health endpoints."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from tests.integration.base import BaseAPIIntegrationTest


class TestHealthEndpoints(BaseAPIIntegrationTest):
    """Tests for health endpoints."""

    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = self.client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Welcome to MAGPIE - MAG Platform for Intelligent Execution"
        assert data["version"] == settings.VERSION
        assert data["status"] == "operational"
        assert data["documentation"] == "/docs"
        assert data["api_version"] == settings.API_V1_STR

    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get(f"{settings.API_V1_STR}/health/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "timestamp" in data
        assert "environment" in data
        assert "services" in data
        assert isinstance(data["services"], dict)

        # Check services status
        services = data["services"]
        assert "database" in services
        assert "redis" in services
        assert "azure_openai" in services

        # Each service should have a status
        for service_name, service_info in services.items():
            assert "status" in service_info
            assert service_info["status"] in ["ok", "error", "unknown"]

            # If status is error, there should be an error message
            if service_info["status"] == "error":
                assert "error" in service_info

            # If status is ok, there should be a latency value
            if service_info["status"] == "ok":
                assert "latency_ms" in service_info
                assert isinstance(service_info["latency_ms"], (int, float))

    def test_readiness_check(self):
        """Test readiness check endpoint."""
        response = self.client.get(f"{settings.API_V1_STR}/health/ready")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] in ["ready", "not_ready"]
        assert "timestamp" in data
        assert "checks" in data
        assert isinstance(data["checks"], list)

        # Check that each check has the required fields
        for check in data["checks"]:
            assert "name" in check
            assert "status" in check
            assert check["status"] in ["passed", "failed"]

            # If check failed, there should be a reason
            if check["status"] == "failed":
                assert "reason" in check

    def test_liveness_check(self):
        """Test liveness check endpoint."""
        response = self.client.get(f"{settings.API_V1_STR}/health/live")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] in ["alive", "not_alive"]
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert "timestamp" in data

    def test_detailed_health_endpoint(self):
        """Test the detailed health endpoint."""
        response = self.client.get(f"{settings.API_V1_STR}/health/detailed")
        assert response.status_code == status.HTTP_200_OK
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
