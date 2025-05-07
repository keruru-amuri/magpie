"""
Unit tests for metrics API endpoints.
"""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.monitoring.metrics import PerformanceMetric
from app.main import app


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def mock_metrics():
    """Create mock metrics for testing."""
    return [
        PerformanceMetric(
            name="http_requests_total",
            value=1,
            unit="count",
            timestamp=datetime(2023, 1, 1, tzinfo=timezone.utc),
            tags={"method": "GET", "path": "/api/v1/test"},
        ),
        PerformanceMetric(
            name="http_request_duration_milliseconds",
            value=123.45,
            unit="ms",
            timestamp=datetime(2023, 1, 1, tzinfo=timezone.utc),
            tags={"method": "GET", "path": "/api/v1/test", "status": "200"},
        ),
    ]


@pytest.mark.parametrize(
    "endpoint,expected_status",
    [
        ("/api/v1/metrics/", status.HTTP_401_UNAUTHORIZED),
        ("/api/v1/metrics/summary", status.HTTP_401_UNAUTHORIZED),
    ],
)
def test_metrics_endpoints_unauthorized(client, endpoint, expected_status):
    """Test that metrics endpoints require authentication."""
    response = client.get(endpoint)
    assert response.status_code == expected_status


@patch("app.api.deps.get_current_superuser")
@patch("app.api.api_v1.endpoints.metrics.get_metrics")
def test_read_metrics(mock_get_metrics, mock_get_user, client, mock_metrics):
    """Test that read_metrics endpoint returns metrics."""
    # Set up mocks
    mock_get_metrics.return_value = mock_metrics
    mock_get_user.return_value = {"id": "test-user", "is_superuser": True}

    # Call endpoint
    response = client.get("/api/v1/metrics/")

    # Check response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 2
    assert len(data["metrics"]) == 2
    assert data["metrics"][0]["name"] == "http_requests_total"
    assert data["metrics"][1]["name"] == "http_request_duration_milliseconds"

    # Check that get_metrics was called with the correct parameters
    mock_get_metrics.assert_called_once_with(None, None, None, 100)


@patch("app.api.deps.get_current_superuser")
@patch("app.api.api_v1.endpoints.metrics.get_metrics")
def test_read_metrics_with_filters(mock_get_metrics, mock_get_user, client, mock_metrics):
    """Test that read_metrics endpoint handles filters correctly."""
    # Set up mocks
    mock_get_metrics.return_value = mock_metrics
    mock_get_user.return_value = {"id": "test-user", "is_superuser": True}

    # Call endpoint with filters
    response = client.get(
        "/api/v1/metrics/",
        params={
            "name": "http_requests_total",
            "start_time": "2023-01-01T00:00:00Z",
            "end_time": "2023-01-02T00:00:00Z",
            "limit": 10,
        },
    )

    # Check response
    assert response.status_code == status.HTTP_200_OK

    # Check that get_metrics was called with the correct parameters
    mock_get_metrics.assert_called_once()
    args, kwargs = mock_get_metrics.call_args
    assert args[0] == "http_requests_total"
    assert args[1].year == 2023
    assert args[1].month == 1
    assert args[1].day == 1
    assert args[2].year == 2023
    assert args[2].month == 1
    assert args[2].day == 2
    assert args[3] == 10


@patch("app.api.deps.get_current_superuser")
@patch("app.api.api_v1.endpoints.metrics.get_metrics")
def test_read_metrics_summary(mock_get_metrics, mock_get_user, client, mock_metrics):
    """Test that read_metrics_summary endpoint returns a summary."""
    # Set up mocks
    mock_get_metrics.side_effect = [
        # http_requests_total
        [
            PerformanceMetric(
                name="http_requests_total",
                value=1,
                unit="count",
                timestamp=datetime(2023, 1, 1, tzinfo=timezone.utc),
                tags={"method": "GET", "path": "/api/v1/test"},
            ),
        ],
        # http_responses_total
        [
            PerformanceMetric(
                name="http_responses_total",
                value=1,
                unit="count",
                timestamp=datetime(2023, 1, 1, tzinfo=timezone.utc),
                tags={"method": "GET", "path": "/api/v1/test", "status": "200"},
            ),
        ],
        # http_errors_total
        [],
        # http_request_duration_milliseconds
        [
            PerformanceMetric(
                name="http_request_duration_milliseconds",
                value=123.45,
                unit="ms",
                timestamp=datetime(2023, 1, 1, tzinfo=timezone.utc),
                tags={"method": "GET", "path": "/api/v1/test", "status": "200"},
            ),
        ],
    ]
    mock_get_user.return_value = {"id": "test-user", "is_superuser": True}

    # Call endpoint
    response = client.get("/api/v1/metrics/summary")

    # Check response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_requests"] == 1
    assert data["total_responses"] == 1
    assert data["total_errors"] == 0
    assert data["average_duration_ms"] == 123.45
    assert "/api/v1/test" in data["paths"]
    assert data["paths"]["/api/v1/test"]["total"] == 1
    assert data["paths"]["/api/v1/test"]["status_codes"]["200"] == 1
