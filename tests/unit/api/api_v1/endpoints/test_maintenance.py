"""
Unit tests for the maintenance endpoints.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.regulatory_requirements_service import RegulatoryRequirementsService


client = TestClient(app)


class TestMaintenanceEndpoints:
    """
    Test cases for the maintenance endpoints.
    """

    @pytest.fixture
    def mock_regulatory_service(self):
        """
        Fixture providing a mock RegulatoryRequirementsService.
        """
        service = MagicMock(spec=RegulatoryRequirementsService)
        service.get_all_requirements.return_value = [
            {
                "id": "reg-faa-001",
                "authority": "FAA",
                "reference_id": "14 CFR 43.13",
                "title": "Performance rules (general)",
                "description": "General performance rules for maintenance"
            },
            {
                "id": "reg-easa-001",
                "authority": "EASA",
                "reference_id": "Part-145",
                "title": "Maintenance Organisation Approvals",
                "description": "Requirements for maintenance organizations"
            }
        ]
        service.get_requirement.return_value = {
            "id": "reg-faa-001",
            "authority": "FAA",
            "reference_id": "14 CFR 43.13",
            "title": "Performance rules (general)",
            "description": "General performance rules for maintenance"
        }
        service.get_requirements_by_authority.return_value = [
            {
                "id": "reg-faa-001",
                "authority": "FAA",
                "reference_id": "14 CFR 43.13",
                "title": "Performance rules (general)",
                "description": "General performance rules for maintenance"
            }
        ]
        service.get_requirements_for_task.return_value = [
            {
                "id": "reg-faa-001",
                "authority": "FAA",
                "reference_id": "14 CFR 43.13",
                "title": "Performance rules (general)",
                "description": "General performance rules for maintenance"
            },
            {
                "id": "reg-easa-001",
                "authority": "EASA",
                "reference_id": "Part-145",
                "title": "Maintenance Organisation Approvals",
                "description": "Requirements for maintenance organizations"
            }
        ]
        return service

    @patch("app.api.api_v1.endpoints.maintenance.RegulatoryRequirementsService")
    def test_get_regulatory_requirements(self, mock_service_class, mock_regulatory_service):
        """
        Test getting all regulatory requirements.
        """
        # Set up the mock
        mock_service_class.return_value = mock_regulatory_service

        # Make the request
        response = client.get("/api/v1/maintenance/regulatory-requirements")

        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 2
        assert data["data"][0]["id"] == "reg-faa-001"
        assert data["data"][1]["id"] == "reg-easa-001"

    @patch("app.api.api_v1.endpoints.maintenance.RegulatoryRequirementsService")
    def test_get_regulatory_requirements_by_authority(self, mock_service_class, mock_regulatory_service):
        """
        Test getting regulatory requirements by authority.
        """
        # Set up the mock
        mock_service_class.return_value = mock_regulatory_service

        # Make the request
        response = client.get("/api/v1/maintenance/regulatory-requirements?authority=FAA")

        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "reg-faa-001"
        assert data["data"][0]["authority"] == "FAA"

    @patch("app.api.api_v1.endpoints.maintenance.RegulatoryRequirementsService")
    def test_get_regulatory_requirement_by_id(self, mock_service_class, mock_regulatory_service):
        """
        Test getting a regulatory requirement by ID.
        """
        # Set up the mock
        mock_service_class.return_value = mock_regulatory_service

        # Make the request
        response = client.get("/api/v1/maintenance/regulatory-requirements/reg-faa-001")

        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["id"] == "reg-faa-001"
        assert data["data"]["authority"] == "FAA"

    @patch("app.api.api_v1.endpoints.maintenance.RegulatoryRequirementsService")
    def test_get_regulatory_requirement_by_id_not_found(self, mock_service_class, mock_regulatory_service):
        """
        Test getting a non-existent regulatory requirement by ID.
        """
        # Set up the mock
        mock_service_class.return_value = mock_regulatory_service
        mock_regulatory_service.get_requirement.return_value = None

        # Make the request
        response = client.get("/api/v1/maintenance/regulatory-requirements/non-existent")

        # Verify the response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]

    @patch("app.api.api_v1.endpoints.maintenance.RegulatoryRequirementsService")
    def test_get_regulatory_requirements_for_task(self, mock_service_class, mock_regulatory_service):
        """
        Test getting regulatory requirements for a specific task.
        """
        # Set up the mock
        mock_service_class.return_value = mock_regulatory_service

        # Make the request
        response = client.get("/api/v1/maintenance/regulatory-requirements/task/inspection/fuel_system")

        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 2
        assert data["data"][0]["id"] == "reg-faa-001"
        assert data["data"][1]["id"] == "reg-easa-001"

    @patch("app.api.api_v1.endpoints.maintenance.MaintenanceAgent")
    def test_validate_procedure_with_regulatory_info(self, mock_agent_class):
        """
        Test validating a procedure with regulatory information.
        """
        # Set up the mock
        mock_agent = MagicMock()
        mock_agent.validate_procedure.return_value.success = True
        mock_agent.validate_procedure.return_value.response = "The maintenance procedure has been validated successfully."
        mock_agent.validate_procedure.return_value.data = {
            "validation_result": "passed",
            "regulatory_validation": {
                "valid": True,
                "requirements": ["14 CFR 43.13", "Part-145"],
                "issues": [],
                "recommendations": ["Consider adding a reference to EASA Part-145 - Maintenance Organisation Approvals"]
            }
        }
        mock_agent_class.return_value = mock_agent

        # Create a test procedure
        procedure = {
            "title": "Test Procedure",
            "description": "Test procedure description",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Test Step",
                    "description": "Test step description"
                }
            ],
            "safety_precautions": ["Test safety precaution"]
        }

        # Make the request
        response = client.post(
            "/api/v1/maintenance/templates/validate",
            json=procedure,
            params={
                "procedure_type": "inspection",
                "system": "fuel_system",
                "aircraft_type": "Boeing 737",
                "aircraft_category": "commercial",
                "jurisdiction": "United States"
            }
        )

        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "validation_result" in data["data"]
        assert data["data"]["validation_result"] == "passed"
        assert "regulatory_validation" in data["data"]
        
        # Verify the agent was called with the correct parameters
        mock_agent.validate_procedure.assert_called_once_with(
            procedure=procedure,
            procedure_type="inspection",
            system="fuel_system",
            aircraft_type="Boeing 737",
            aircraft_category="commercial",
            jurisdiction="United States"
        )
