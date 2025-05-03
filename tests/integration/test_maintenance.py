"""Integration tests for maintenance endpoints."""

import pytest
from fastapi import status

from app.core.config import settings
from tests.integration.base import BaseAPIIntegrationTest

# Mark all tests in this module as skipped until the endpoints are implemented
pytestmark = pytest.mark.skip(reason="Maintenance endpoints not yet implemented")


class TestMaintenanceEndpoints(BaseAPIIntegrationTest):
    """Tests for maintenance endpoints."""

    def test_get_maintenance_procedures_list(self):
        """Test getting the list of maintenance procedures."""
        response = self.client.get(f"{settings.API_V1_STR}/maintenance/procedures")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Maintenance procedures retrieved successfully"
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

        # Verify structure of procedure items
        procedure_item = data["data"][0]
        assert "id" in procedure_item
        assert "title" in procedure_item
        assert "aircraft_type" in procedure_item
        assert "system" in procedure_item
        assert "task_type" in procedure_item
        assert "estimated_duration" in procedure_item
        assert "last_updated" in procedure_item

    def test_get_maintenance_procedure_by_id_valid(self):
        """Test getting maintenance procedure by valid ID."""
        valid_procedure_id = "proc-001"
        response = self.client.get(f"{settings.API_V1_STR}/maintenance/procedures/{valid_procedure_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == f"Maintenance procedure {valid_procedure_id} retrieved successfully"
        assert "data" in data

        # Verify structure of procedure data
        procedure_data = data["data"]
        assert procedure_data["id"] == valid_procedure_id
        assert "title" in procedure_data
        assert "aircraft_type" in procedure_data
        assert "system" in procedure_data
        assert "task_type" in procedure_data
        assert "estimated_duration" in procedure_data
        assert "last_updated" in procedure_data
        assert "steps" in procedure_data
        assert isinstance(procedure_data["steps"], list)
        assert len(procedure_data["steps"]) > 0
        assert "tools_required" in procedure_data
        assert isinstance(procedure_data["tools_required"], list)
        assert "safety_precautions" in procedure_data
        assert isinstance(procedure_data["safety_precautions"], list)

    def test_get_maintenance_procedure_by_id_invalid(self):
        """Test getting maintenance procedure by invalid ID."""
        invalid_procedure_id = "invalid-proc-id"
        response = self.client.get(f"{settings.API_V1_STR}/maintenance/procedures/{invalid_procedure_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert f"Maintenance procedure with ID {invalid_procedure_id} not found" in data["detail"]

    def test_generate_maintenance_procedure(self):
        """Test generating a maintenance procedure."""
        procedure_request = {
            "aircraft_type": "Airbus A320",
            "system": "Landing Gear",
            "task_description": "Inspect and service the main landing gear assembly",
            "maintenance_level": "Line",
            "available_tools": ["Standard toolkit", "Hydraulic jack", "Pressure gauge"],
            "technician_experience": "Intermediate"
        }
        response = self.client.post(
            f"{settings.API_V1_STR}/maintenance/generate",
            json=procedure_request
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Maintenance procedure generated successfully"
        assert "data" in data

        # Verify structure of generated procedure
        procedure = data["data"]
        assert "procedure_id" in procedure
        assert "title" in procedure
        assert "aircraft_type" in procedure
        assert "system" in procedure
        assert "task_type" in procedure
        assert "estimated_duration" in procedure
        assert "tools_required" in procedure
        assert isinstance(procedure["tools_required"], list)
        assert "safety_precautions" in procedure
        assert isinstance(procedure["safety_precautions"], list)
        assert "steps" in procedure
        assert isinstance(procedure["steps"], list)
        assert len(procedure["steps"]) > 0

        # Verify structure of procedure steps
        step = procedure["steps"][0]
        assert "step_number" in step
        assert "title" in step
        assert "description" in step
        assert "cautions" in step
        assert "estimated_time" in step
