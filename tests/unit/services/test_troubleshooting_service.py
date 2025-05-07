"""
Unit tests for the troubleshooting service.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.troubleshooting_service import TroubleshootingService


class TestTroubleshootingService:
    """
    Test suite for the TroubleshootingService class.
    """

    @pytest.fixture
    def mock_service(self):
        """
        Create a mock data service for testing.
        """
        mock_service = MagicMock()
        return mock_service

    @pytest.fixture
    def troubleshooting_service(self, mock_service):
        """
        Create a troubleshooting service with a mock data service.
        """
        return TroubleshootingService(mock_service=mock_service)

    def test_get_systems(self, troubleshooting_service, mock_service):
        """
        Test getting available systems.
        """
        # Setup
        mock_systems = [
            {"id": "sys-001", "name": "Hydraulic System"},
            {"id": "sys-002", "name": "Electrical System"}
        ]
        mock_service.get_troubleshooting_systems.return_value = mock_systems

        # Execute
        result = troubleshooting_service.get_systems()

        # Verify
        assert result == mock_systems
        mock_service.get_troubleshooting_systems.assert_called_once()

    def test_get_symptoms(self, troubleshooting_service, mock_service):
        """
        Test getting symptoms for a system.
        """
        # Setup
        system_id = "sys-001"
        mock_symptoms = [
            {"id": "sym-001", "description": "Pressure fluctuation", "severity": "medium"},
            {"id": "sym-002", "description": "Fluid leakage", "severity": "high"}
        ]
        mock_service.get_troubleshooting_symptoms.return_value = {
            "system_id": system_id,
            "system_name": "Hydraulic System",
            "symptoms": mock_symptoms
        }

        # Execute
        result = troubleshooting_service.get_symptoms(system_id)

        # Verify
        assert result == mock_symptoms
        mock_service.get_troubleshooting_symptoms.assert_called_once_with(system_id)

    def test_diagnose_issue(self, troubleshooting_service, mock_service):
        """
        Test diagnosing an issue.
        """
        # Setup
        system = "sys-001"
        symptoms = ["sym-001", "sym-002"]
        context = "Routine maintenance inspection"

        mock_analysis = {
            "request": {
                "system": system,
                "symptoms": symptoms,
                "context": context
            },
            "analysis": {
                "potential_causes": [
                    {
                        "id": "cause-001",
                        "description": "Component wear and tear",
                        "probability": 0.75
                    }
                ],
                "recommended_solutions": [
                    {
                        "id": "sol-001",
                        "description": "Replace component",
                        "difficulty": "medium"
                    }
                ]
            }
        }

        mock_service.analyze_troubleshooting.return_value = mock_analysis

        # Execute
        result = troubleshooting_service.diagnose_issue(system, symptoms, context)

        # Verify
        assert result == mock_analysis
        mock_service.analyze_troubleshooting.assert_called_once_with({
            "system": system,
            "symptoms": symptoms,
            "context": context
        })

    def test_diagnose_issue_with_maintenance_history(self, troubleshooting_service, mock_service):
        """
        Test diagnosing an issue with maintenance history.
        """
        # Setup
        system = "sys-001"
        symptoms = ["sym-001", "sym-002"]
        context = "Routine maintenance inspection"

        maintenance_history = {
            "aircraft_id": "ac-001",
            "system_id": system,
            "recent_events": [
                {
                    "id": "event-001",
                    "date": "2025-03-15",
                    "type": "inspection",
                    "description": "Routine inspection of hydraulic system",
                    "findings": "No issues found"
                }
            ]
        }

        mock_analysis = {
            "request": {
                "system": system,
                "symptoms": symptoms,
                "context": context
            },
            "analysis": {
                "potential_causes": [
                    {
                        "id": "cause-001",
                        "description": "Component wear and tear",
                        "probability": 0.75
                    }
                ],
                "recommended_solutions": [
                    {
                        "id": "sol-001",
                        "description": "Replace component",
                        "difficulty": "medium"
                    }
                ]
            }
        }

        mock_service.analyze_troubleshooting.return_value = mock_analysis

        # Execute
        result = troubleshooting_service.diagnose_issue(
            system, symptoms, context, maintenance_history
        )

        # Verify
        # We're mocking the analyze_troubleshooting method, so the result will be the same as mock_analysis
        # In a real implementation, the result would be adjusted based on maintenance history
        assert result is not None
        mock_service.analyze_troubleshooting.assert_called_once_with({
            "system": system,
            "symptoms": symptoms,
            "context": context
        })

    def test_generate_troubleshooting_procedure(self, troubleshooting_service, mock_service):
        """
        Test generating a troubleshooting procedure.
        """
        # Setup
        system_id = "sys-001"
        cause_id = "cause-001"

        mock_analysis = {
            "request": {
                "system": system_id,
                "symptoms": [],
                "context": ""
            },
            "analysis": {
                "recommended_solutions": [
                    {
                        "id": "sol-001",
                        "description": "Replace component",
                        "difficulty": "medium",
                        "estimated_time": "2 hours",
                        "steps": [
                            "Step 1: Prepare necessary tools",
                            "Step 2: Remove access panels"
                        ]
                    }
                ]
            }
        }

        mock_service.analyze_troubleshooting.return_value = mock_analysis
        mock_service.load_file.return_value = mock_analysis

        # Execute
        result = troubleshooting_service.generate_troubleshooting_procedure(
            system_id, cause_id
        )

        # Verify
        assert "solution" in result
        assert "parts_and_tools" in result
        assert "safety_precautions" in result
        mock_service.analyze_troubleshooting.assert_called_once()

    def test_get_safety_precautions(self, troubleshooting_service):
        """
        Test getting safety precautions for a system.
        """
        # Setup
        system_id = "sys-001"  # Hydraulic System

        # Execute
        result = troubleshooting_service._get_safety_precautions(system_id)

        # Verify
        assert len(result) > 0
        assert any("hydraulic" in precaution.lower() for precaution in result)

    def test_get_parts_and_tools(self, troubleshooting_service):
        """
        Test getting parts and tools for a solution.
        """
        # Setup
        system_id = "sys-001"
        solution_id = "sol-001"

        # Execute
        result = troubleshooting_service._get_parts_and_tools(system_id, solution_id)

        # Verify
        assert "parts" in result
        assert "tools" in result
        assert len(result["parts"]) > 0
        assert len(result["tools"]) > 0
