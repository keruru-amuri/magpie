"""Tests for API router."""

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to MAGPIE - MAG Platform for Intelligent Execution"
    assert data["version"] == settings.VERSION
    assert data["status"] == "operational"
    assert data["documentation"] == "/docs"
    assert data["api_version"] == settings.API_V1_STR


def test_docs_endpoint():
    """Test the docs endpoint."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_redoc_endpoint():
    """Test the redoc endpoint."""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_openapi_endpoint():
    """Test the OpenAPI endpoint."""
    response = client.get(f"{settings.API_V1_STR}/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == settings.PROJECT_NAME
    assert data["info"]["version"] == settings.VERSION
