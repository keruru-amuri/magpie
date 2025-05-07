"""
Unit tests for the maintenance formatting endpoints.
"""
import json
from unittest.mock import patch, MagicMock

import pytest
from fastapi import status, FastAPI
from fastapi.testclient import TestClient

from app.api.api_v1.endpoints.maintenance import router as maintenance_router


# Create a test app with the maintenance router
test_app = FastAPI()
test_app.include_router(maintenance_router)

client = TestClient(test_app)

# Global mock agent
mock_agent = MagicMock()
mock_agent._validate_llm_procedure.return_value = True
mock_agent._format_llm_procedure_as_markdown.return_value = "# Test Procedure\n\nTest markdown content"
mock_agent._enrich_procedure_with_regulatory_info.return_value = {"id": "enriched-001", "title": "Enriched Procedure"}
mock_agent.generate_procedure_with_llm.return_value = {
    "id": "maint-001",
    "title": "Test Procedure",
    "description": "Test procedure description",
    "steps": [
        {
            "step_number": 1,
            "title": "Test Step",
            "description": "Test step description"
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
mock_agent.enhance_procedure_with_llm.return_value = {
    "id": "maint-001",
    "title": "Enhanced Test Procedure",
    "description": "Enhanced test procedure description",
    "steps": [
        {
            "step_number": 1,
            "title": "Test Step",
            "description": "Test step description"
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
mock_agent.generate_procedure.return_value = {
    "request": {
        "aircraft_type": "Boeing 737",
        "system": "Hydraulic",
        "procedure_type": "Inspection",
        "parameters": {}
    },
    "procedure": {
        "id": "maint-001",
        "title": "Test Procedure",
        "description": "Test procedure description",
        "steps": [
            {
                "step_number": 1,
                "title": "Test Step",
                "description": "Test step description"
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
}

# Override the dependency
def override_get_maintenance_agent():
    return mock_agent

from app.api.api_v1.endpoints.maintenance import get_maintenance_agent
test_app.dependency_overrides[get_maintenance_agent] = override_get_maintenance_agent


class TestMaintenanceFormatEndpoints:
    """
    Test cases for the maintenance formatting endpoints.
    """

    def test_format_procedure_as_json(self):
        """
        Test formatting a procedure as JSON.
        """
        # Test procedure
        procedure = {
            "id": "maint-001",
            "title": "Test Procedure",
            "description": "Test procedure description",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Test Step",
                    "description": "Test step description"
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
            "/maintenance/format-procedure",
            params={"format_type": "json"},
            json=procedure
        )

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Maintenance procedure formatted successfully"
        assert data["data"]["format"] == "json"
        assert data["data"]["procedure"] == procedure

        # Verify agent was called
        mock_agent._validate_llm_procedure.assert_called_once_with(procedure)

    def test_format_procedure_as_markdown(self):
        """
        Test formatting a procedure as markdown.
        """
        # Reset mocks
        mock_agent._validate_llm_procedure.reset_mock()
        mock_agent._format_llm_procedure_as_markdown.reset_mock()

        # Test procedure
        procedure = {
            "id": "maint-001",
            "title": "Test Procedure",
            "description": "Test procedure description",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Test Step",
                    "description": "Test step description"
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
            "/maintenance/format-procedure",
            params={"format_type": "markdown"},
            json=procedure
        )

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Maintenance procedure formatted successfully"
        assert data["data"]["format"] == "markdown"
        assert data["data"]["procedure"] == "# Test Procedure\n\nTest markdown content"

        # Verify agent was called
        assert mock_agent._validate_llm_procedure.call_count > 0
        assert mock_agent._format_llm_procedure_as_markdown.call_count > 0

    def test_format_procedure_with_regulatory_enrichment(self):
        """
        Test formatting a procedure with regulatory enrichment.
        """
        # Reset mocks
        mock_agent._validate_llm_procedure.reset_mock()
        mock_agent._enrich_procedure_with_regulatory_info.reset_mock()

        # Test procedure
        procedure = {
            "id": "maint-001",
            "title": "Test Procedure",
            "description": "Test procedure description",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Test Step",
                    "description": "Test step description"
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
            "/maintenance/format-procedure",
            params={
                "format_type": "json",
                "enrich_regulatory": "true",
                "regulatory_requirements": "FAA Part 43"
            },
            json=procedure
        )

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Maintenance procedure formatted successfully"
        assert data["data"]["format"] == "json"
        assert data["data"]["procedure"] == {"id": "enriched-001", "title": "Enriched Procedure"}

        # Verify agent was called
        assert mock_agent._validate_llm_procedure.call_count > 0
        assert mock_agent._enrich_procedure_with_regulatory_info.call_count > 0

    def test_format_procedure_invalid(self):
        """
        Test formatting an invalid procedure.
        """
        # Configure mock to fail validation
        mock_agent._validate_llm_procedure.reset_mock()
        mock_agent._validate_llm_procedure.return_value = False

        # Test procedure (invalid)
        procedure = {
            "id": "maint-001",
            "title": "Test Procedure"
            # Missing required fields
        }

        # Make request
        response = client.post(
            "/maintenance/format-procedure",
            params={"format_type": "json"},
            json=procedure
        )

        # Verify response
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["detail"] == "Invalid procedure format"

        # Reset the mock for future tests
        mock_agent._validate_llm_procedure.reset_mock()
        mock_agent._validate_llm_procedure.return_value = True

    def test_generate_procedure_with_llm_markdown(self):
        """
        Test generating a procedure with LLM and formatting as markdown.
        """
        # Configure mock
        mock_agent.generate_procedure_with_llm.reset_mock()
        mock_agent._format_llm_procedure_as_markdown.reset_mock()

        mock_procedure = {
            "id": "maint-001",
            "title": "Test Procedure",
            "description": "Test procedure description",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Test Step",
                    "description": "Test step description"
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
        response = client.post(
            "/maintenance/generate-with-llm",
            params={"format_type": "markdown"},
            json=request_data
        )

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Maintenance procedure generated successfully with LLM"
        assert data["data"]["format"] == "markdown"
        assert data["data"]["procedure"] == "# Test Procedure\n\nTest markdown content"

        # Verify agent was called
        mock_agent.generate_procedure_with_llm.assert_called_once()
        mock_agent._format_llm_procedure_as_markdown.assert_called_once_with(mock_procedure)

    def test_generate_hybrid_procedure_markdown(self):
        """
        Test generating a procedure with hybrid approach and formatting as markdown.
        """
        # Configure mock
        mock_agent.generate_procedure.reset_mock()
        mock_agent._format_llm_procedure_as_markdown.reset_mock()

        mock_result = {
            "request": {
                "aircraft_type": "Boeing 737",
                "system": "Hydraulic",
                "procedure_type": "Inspection",
                "parameters": {}
            },
            "procedure": {
                "id": "maint-001",
                "title": "Test Procedure",
                "description": "Test procedure description",
                "steps": [
                    {
                        "step_number": 1,
                        "title": "Test Step",
                        "description": "Test step description"
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
        }
        mock_agent.generate_procedure.return_value = mock_result

        # Make request
        request_data = {
            "aircraft_type": "Boeing 737",
            "system": "Hydraulic",
            "procedure_type": "Inspection",
            "parameters": {
                "regulatory_requirements": "FAA regulations"
            }
        }
        response = client.post(
            "/maintenance/generate-hybrid",
            params={"format_type": "markdown"},
            json=request_data
        )

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Maintenance procedure generated successfully with hybrid approach"
        assert data["data"]["format"] == "markdown"
        assert data["data"]["procedure"] == "# Test Procedure\n\nTest markdown content"
        assert data["data"]["generation_method"] == "llm"  # No template_id in the mock procedure

        # Verify agent was called
        mock_agent.generate_procedure.assert_called_once()
        mock_agent._format_llm_procedure_as_markdown.assert_called_once_with(mock_result["procedure"])
