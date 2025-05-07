"""
Unit tests for analytics API endpoints.
"""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_superuser
from app.core.monitoring import ModelSize, AnalyticsPeriod
from app.main import app


# Override the dependency for testing
async def mock_superuser():
    return {"id": "test_user", "is_superuser": True}

app.dependency_overrides[get_current_superuser] = mock_superuser

# Create the test client with the overridden dependency
client = TestClient(app)


@pytest.fixture
def mock_get_usage_records():
    """Mock the get_usage_records function."""
    with patch("app.api.api_v1.endpoints.analytics.get_usage_records") as mock:
        mock.return_value = [
            {
                "id": "test_usage_1",
                "timestamp": datetime.now(timezone.utc),
                "model_size": ModelSize.MEDIUM,
                "agent_type": "test_agent",
                "user_id": "test_user",
                "conversation_id": "test_conversation",
                "request_id": "test_request",
                "input_tokens": 1000,
                "output_tokens": 500,
                "total_tokens": 1500,
                "cost": 0.0012,
                "latency_ms": 150.5,
            }
        ]
        yield mock


@pytest.fixture
def mock_get_user_metrics():
    """Mock the get_user_metrics function."""
    with patch("app.api.api_v1.endpoints.analytics.get_user_metrics") as mock:
        mock.return_value = {
            "user_id": "test_user",
            "period": AnalyticsPeriod.DAILY,
            "metrics": {
                "request_count": 10,
                "input_tokens": 10000,
                "output_tokens": 5000,
                "total_tokens": 15000,
                "cost": 0.012,
            },
        }
        yield mock


@pytest.fixture
def mock_get_model_metrics():
    """Mock the get_model_metrics function."""
    with patch("app.api.api_v1.endpoints.analytics.get_model_metrics") as mock:
        mock.return_value = {
            "model_size": ModelSize.MEDIUM,
            "period": AnalyticsPeriod.DAILY,
            "metrics": {
                "request_count": 10,
                "input_tokens": 10000,
                "output_tokens": 5000,
                "total_tokens": 15000,
                "cost": 0.012,
            },
        }
        yield mock


@pytest.fixture
def mock_get_agent_metrics():
    """Mock the get_agent_metrics function."""
    with patch("app.api.api_v1.endpoints.analytics.get_agent_metrics") as mock:
        mock.return_value = {
            "agent_type": "test_agent",
            "period": AnalyticsPeriod.DAILY,
            "metrics": {
                "request_count": 10,
                "input_tokens": 10000,
                "output_tokens": 5000,
                "total_tokens": 15000,
                "cost": 0.012,
            },
        }
        yield mock


@pytest.fixture
def mock_get_global_metrics():
    """Mock the get_global_metrics function."""
    with patch("app.api.api_v1.endpoints.analytics.get_global_metrics") as mock:
        mock.return_value = {
            "period": AnalyticsPeriod.DAILY,
            "metrics": {
                "request_count": 10,
                "input_tokens": 10000,
                "output_tokens": 5000,
                "total_tokens": 15000,
                "cost": 0.012,
            },
        }
        yield mock


def test_read_usage_records(mock_get_usage_records):
    """Test the read_usage_records endpoint."""
    response = client.get("/api/v1/analytics/usage")

    assert response.status_code == 200
    data = response.json()
    assert "records" in data
    assert "count" in data
    assert data["count"] == 1

    mock_get_usage_records.assert_called_once()


def test_read_user_metrics(mock_get_user_metrics):
    """Test the read_user_metrics endpoint."""
    response = client.get("/api/v1/analytics/user/test_user")

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test_user"
    assert data["period"] == "daily"
    assert "metrics" in data

    mock_get_user_metrics.assert_called_once()


def test_read_model_metrics(mock_get_model_metrics):
    """Test the read_model_metrics endpoint."""
    response = client.get("/api/v1/analytics/model/medium")

    assert response.status_code == 200
    data = response.json()
    assert data["model_size"] == "medium"
    assert data["period"] == "daily"
    assert "metrics" in data

    mock_get_model_metrics.assert_called_once()


def test_read_agent_metrics(mock_get_agent_metrics):
    """Test the read_agent_metrics endpoint."""
    response = client.get("/api/v1/analytics/agent/test_agent")

    assert response.status_code == 200
    data = response.json()
    assert data["agent_type"] == "test_agent"
    assert data["period"] == "daily"
    assert "metrics" in data

    mock_get_agent_metrics.assert_called_once()


def test_read_global_metrics(mock_get_global_metrics):
    """Test the read_global_metrics endpoint."""
    response = client.get("/api/v1/analytics/global")

    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "daily"
    assert "metrics" in data

    mock_get_global_metrics.assert_called_once()


def test_read_analytics_summary(
    mock_get_global_metrics,
    mock_get_model_metrics,
):
    """Test the read_analytics_summary endpoint."""
    response = client.get("/api/v1/analytics/summary")

    assert response.status_code == 200
    data = response.json()
    assert "daily" in data
    assert "weekly" in data
    assert "monthly" in data
    assert "all_time" in data
    assert "models" in data

    assert mock_get_global_metrics.call_count == 4
    assert mock_get_model_metrics.call_count == 3
