"""Tests for the main application module."""

from fastapi.testclient import TestClient

from app.core.config import settings


def test_root_endpoint(client: TestClient):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to MAGPIE - MAG Platform for Intelligent Execution"
    assert data["version"] == settings.VERSION
    assert data["status"] == "operational"


def test_health_check(client: TestClient):
    """Test the health check endpoint."""
    response = client.get(f"{settings.API_V1_STR}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "debug" in data
    assert data["version"] == settings.VERSION
