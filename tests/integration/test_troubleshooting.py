"""Integration tests for troubleshooting endpoints."""

import pytest
from fastapi import status

from app.core.config import settings
from tests.integration.base import BaseAPIIntegrationTest

# Mark all tests in this module as skipped until the endpoints are implemented
pytestmark = pytest.mark.skip(reason="Troubleshooting endpoints not yet implemented")


class TestTroubleshootingEndpoints(BaseAPIIntegrationTest):
    """Tests for troubleshooting endpoints."""

    def test_get_troubleshooting_list(self):
        """Test getting the list of troubleshooting guides."""
        response = self.client.get(f"{settings.API_V1_STR}/troubleshooting/guides")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Troubleshooting guides retrieved successfully"
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

        # Verify structure of guide items
        guide_item = data["data"][0]
        assert "id" in guide_item
        assert "title" in guide_item
        assert "aircraft_type" in guide_item
        assert "system" in guide_item
        assert "last_updated" in guide_item

    def test_get_troubleshooting_guide_by_id_valid(self):
        """Test getting troubleshooting guide by valid ID."""
        valid_guide_id = "guide-001"
        response = self.client.get(f"{settings.API_V1_STR}/troubleshooting/guides/{valid_guide_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == f"Troubleshooting guide {valid_guide_id} retrieved successfully"
        assert "data" in data

        # Verify structure of guide data
        guide_data = data["data"]
        assert guide_data["id"] == valid_guide_id
        assert "title" in guide_data
        assert "aircraft_type" in guide_data
        assert "system" in guide_data
        assert "last_updated" in guide_data
        assert "steps" in guide_data
        assert isinstance(guide_data["steps"], list)
        assert len(guide_data["steps"]) > 0

    def test_get_troubleshooting_guide_by_id_invalid(self):
        """Test getting troubleshooting guide by invalid ID."""
        invalid_guide_id = "invalid-guide-id"
        response = self.client.get(f"{settings.API_V1_STR}/troubleshooting/guides/{invalid_guide_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert f"Troubleshooting guide with ID {invalid_guide_id} not found" in data["detail"]

    def test_analyze_issue(self):
        """Test analyzing an issue."""
        issue_data = {
            "aircraft_type": "Boeing 737-800",
            "system": "Hydraulic",
            "symptoms": ["Pressure fluctuation", "Unusual noise"],
            "observed_conditions": "During cruise at 30,000 feet, hydraulic pressure gauge shows fluctuations between 2800-3200 psi with accompanying noise from the pump area."
        }
        response = self.client.post(
            f"{settings.API_V1_STR}/troubleshooting/analyze",
            json=issue_data
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Issue analysis completed successfully"
        assert "data" in data

        # Verify structure of analysis results
        analysis_data = data["data"]
        assert "issue_id" in analysis_data
        assert "aircraft_type" in analysis_data
        assert "system" in analysis_data
        assert "symptoms" in analysis_data
        assert "possible_causes" in analysis_data
        assert isinstance(analysis_data["possible_causes"], list)
        assert len(analysis_data["possible_causes"]) > 0
        assert "recommended_actions" in analysis_data
        assert isinstance(analysis_data["recommended_actions"], list)
        assert len(analysis_data["recommended_actions"]) > 0
        assert "related_guides" in analysis_data
        assert isinstance(analysis_data["related_guides"], list)

        # Verify structure of possible causes
        cause = analysis_data["possible_causes"][0]
        assert "description" in cause
        assert "probability" in cause
        assert 0 <= cause["probability"] <= 1

        # Verify structure of recommended actions
        action = analysis_data["recommended_actions"][0]
        assert "step" in action
        assert "description" in action
        assert "expected_outcome" in action
