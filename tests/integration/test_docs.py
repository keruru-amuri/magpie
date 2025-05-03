"""Integration tests for documentation endpoints."""

import pytest
from fastapi import status

from app.core.config import settings
from tests.integration.base import BaseAPIIntegrationTest


class TestDocumentationUIEndpoints(BaseAPIIntegrationTest):
    """Tests for documentation UI endpoints."""

    def test_swagger_ui(self):
        """Test Swagger UI endpoint."""
        response = self.client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
        assert "swagger-ui" in response.text.lower()

    def test_redoc_ui(self):
        """Test ReDoc UI endpoint."""
        response = self.client.get("/redoc")
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
        assert "redoc" in response.text.lower()

    def test_openapi_json(self):
        """Test OpenAPI JSON endpoint."""
        response = self.client.get(f"{settings.API_V1_STR}/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        assert "application/json" in response.headers["content-type"]
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
        assert "components" in data

        # Check API info
        assert data["info"]["title"] == settings.PROJECT_NAME
        assert data["info"]["version"] == settings.VERSION

        # Check that our endpoints are documented
        assert f"{settings.API_V1_STR}/health/health" in data["paths"]

        # Check that at least one endpoint from each module is documented
        # These assertions are commented out until the endpoints are implemented
        # assert f"{settings.API_V1_STR}/documentation/documentation" in data["paths"]
        # assert f"{settings.API_V1_STR}/troubleshooting/guides" in data["paths"]
        # assert f"{settings.API_V1_STR}/maintenance/procedures" in data["paths"]

    def test_swagger_oauth_redirect(self):
        """Test Swagger UI OAuth redirect endpoint."""
        # Get the actual OAuth redirect URL from the app
        oauth_redirect_url = self.app.swagger_ui_oauth2_redirect_url
        response = self.client.get(oauth_redirect_url)
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
