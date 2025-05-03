"""Tests for health endpoints."""

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "debug" in data
    assert data["version"] == settings.VERSION


def test_detailed_health_endpoint():
    """Test the detailed health endpoint."""
    response = client.get("/api/v1/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "api" in data
    assert "database" in data
    assert "redis" in data
    assert "azure_openai" in data
    assert data["api"]["version"] == settings.VERSION
