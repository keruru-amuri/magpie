"""
Unit tests for the maintenance LLM-based endpoints.
"""
import json
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi import status, FastAPI, Depends
from fastapi.testclient import TestClient

from app.services.llm_service import ModelSize
from app.api.api_v1.endpoints.maintenance import router as maintenance_router, get_maintenance_agent
from app.core.agents.maintenance_agent import MaintenanceAgent


# Create a mock maintenance agent
mock_agent = AsyncMock()
mock_agent.generate_procedure_with_llm = AsyncMock()
mock_agent.enhance_procedure_with_llm = AsyncMock()

# Override the dependency
async def override_get_maintenance_agent():
    return mock_agent

# Create a test app with the maintenance router
test_app = FastAPI()
test_app.include_router(maintenance_router)
test_app.dependency_overrides[get_maintenance_agent] = override_get_maintenance_agent

client = TestClient(test_app)


class TestMaintenanceLLMEndpoints:
    """
    Test cases for the maintenance LLM-based endpoints.
    """

    def test_generate_procedure_with_llm(self):
        """
        Test generating a procedure with LLM.
        """
        # Configure mock
        mock_procedure = {
            "id": "maint-001",
            "title": "Test Procedure",
            "description": "Test procedure description",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Test Step",
                    "description": "Test step description",
                    "cautions": ["Test caution"]
                }
            ],
            "safety_precautions": ["Test safety precaution"],
            "tools_required": [
                {
                    "id": "tool-001",
                    "name": "Test Tool",
                    "specification": "Test specification"
                }
            ]
        }
        mock_agent.generate_procedure_with_llm.return_value = mock_procedure

        # Make request
        request_data = {
            "procedure_type": "Inspection",
            "aircraft_type": "Boeing 737",
            "aircraft_model": "737-800",
            "system": "Hydraulic",
            "components": "Pumps, Reservoirs",
            "configuration": "Standard configuration",
            "regulatory_requirements": "FAA regulations",
            "special_considerations": "None",
            "use_large_model": True
        }
        response = client.post("/maintenance/generate-with-llm", json=request_data)

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "Maintenance procedure generated successfully" in data["message"]
        assert data["data"]["procedure"] == mock_procedure
        assert data["data"]["request"] == request_data

        # Verify agent was called with correct parameters
        mock_agent.generate_procedure_with_llm.assert_called_once()
        _, kwargs = mock_agent.generate_procedure_with_llm.call_args
        assert kwargs["procedure_type"] == "Inspection"
        assert kwargs["aircraft_type"] == "Boeing 737"
        assert kwargs["aircraft_model"] == "737-800"
        assert kwargs["system"] == "Hydraulic"
        assert kwargs["components"] == "Pumps, Reservoirs"
        assert kwargs["configuration"] == "Standard configuration"
        assert kwargs["regulatory_requirements"] == "FAA regulations"
        assert kwargs["special_considerations"] == "None"
        assert kwargs["model_size"] == ModelSize.LARGE

    def test_generate_procedure_with_llm_failure(self):
        """
        Test generating a procedure with LLM when it fails.
        """
        # Configure mock
        mock_agent.generate_procedure_with_llm.return_value = None

        # Make request
        request_data = {
            "procedure_type": "Inspection",
            "aircraft_type": "Boeing 737",
            "aircraft_model": "737-800",
            "system": "Hydraulic",
            "components": "Pumps, Reservoirs",
            "configuration": "Standard configuration",
            "regulatory_requirements": "FAA regulations",
            "special_considerations": "None",
            "use_large_model": False
        }
        response = client.post("/maintenance/generate-with-llm", json=request_data)

        # Verify response
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["detail"] == "Failed to generate procedure with LLM"

    def test_enhance_procedure_with_llm(self):
        """
        Test enhancing a procedure with LLM.
        """
        # Configure mock
        mock_enhanced_procedure = {
            "id": "maint-001",
            "title": "Enhanced Test Procedure",
            "description": "Enhanced test procedure description",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Enhanced Test Step",
                    "description": "Enhanced test step description",
                    "cautions": ["Enhanced test caution"]
                }
            ],
            "safety_precautions": ["Enhanced test safety precaution"],
            "tools_required": [
                {
                    "id": "tool-001",
                    "name": "Enhanced Test Tool",
                    "specification": "Enhanced test specification"
                }
            ]
        }
        mock_agent.enhance_procedure_with_llm.return_value = mock_enhanced_procedure

        # Base procedure to enhance
        base_procedure = {
            "id": "maint-001",
            "title": "Test Procedure",
            "description": "Test procedure description",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Test Step",
                    "description": "Test step description",
                    "cautions": ["Test caution"]
                }
            ],
            "safety_precautions": ["Test safety precaution"],
            "tools_required": [
                {
                    "id": "tool-001",
                    "name": "Test Tool",
                    "specification": "Test specification"
                }
            ]
        }

        # Make request
        response = client.post(
            "/maintenance/enhance-with-llm",
            params={
                "aircraft_type": "Boeing 737",
                "aircraft_model": "737-800",
                "system": "Hydraulic",
                "components": "Pumps, Reservoirs",
                "configuration": "Standard configuration",
                "regulatory_requirements": "FAA regulations",
                "special_considerations": "None",
                "use_large_model": "true"
            },
            json=base_procedure
        )

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "Maintenance procedure enhanced successfully" in data["message"]
        assert data["data"]["procedure"] == mock_enhanced_procedure
        assert data["data"]["request"]["aircraft_type"] == "Boeing 737"
        assert data["data"]["request"]["aircraft_model"] == "737-800"
        assert data["data"]["request"]["system"] == "Hydraulic"

        # Verify agent was called with correct parameters
        mock_agent.enhance_procedure_with_llm.assert_called_once()
        _, kwargs = mock_agent.enhance_procedure_with_llm.call_args
        assert kwargs["base_procedure"] == base_procedure
        assert kwargs["aircraft_type"] == "Boeing 737"
        assert kwargs["aircraft_model"] == "737-800"
        assert kwargs["system"] == "Hydraulic"
        assert kwargs["components"] == "Pumps, Reservoirs"
        assert kwargs["configuration"] == "Standard configuration"
        assert kwargs["regulatory_requirements"] == "FAA regulations"
        assert kwargs["special_considerations"] == "None"
        assert kwargs["model_size"] == ModelSize.LARGE

    def test_enhance_procedure_with_llm_failure(self):
        """
        Test enhancing a procedure with LLM when it fails.
        """
        # Configure mock
        mock_agent.enhance_procedure_with_llm.return_value = None

        # Base procedure to enhance
        base_procedure = {
            "id": "maint-001",
            "title": "Test Procedure",
            "description": "Test procedure description",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Test Step",
                    "description": "Test step description",
                    "cautions": ["Test caution"]
                }
            ],
            "safety_precautions": ["Test safety precaution"],
            "tools_required": [
                {
                    "id": "tool-001",
                    "name": "Test Tool",
                    "specification": "Test specification"
                }
            ]
        }

        # Make request
        response = client.post(
            "/maintenance/enhance-with-llm",
            params={
                "aircraft_type": "Boeing 737",
                "aircraft_model": "737-800",
                "system": "Hydraulic"
            },
            json=base_procedure
        )

        # Verify response
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["detail"] == "Failed to enhance procedure with LLM"
