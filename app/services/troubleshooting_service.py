"""
Troubleshooting service for the MAGPIE platform.

This service provides functionality for diagnosing aircraft system issues
and generating troubleshooting procedures.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
import json
from pathlib import Path

from app.core.mock.service import mock_data_service
from app.core.mock.config import MockDataSource

# Configure logging
logger = logging.getLogger(__name__)


class TroubleshootingService:
    """
    Service for troubleshooting aircraft system issues.
    """

    def __init__(self, mock_service=None):
        """
        Initialize troubleshooting service.

        Args:
            mock_service: Optional mock data service for testing
        """
        self.mock_service = mock_service or mock_data_service

    def get_systems(self) -> List[Dict[str, Any]]:
        """
        Get available aircraft systems for troubleshooting.

        Returns:
            List[Dict[str, Any]]: List of available systems
        """
        try:
            return self.mock_service.get_troubleshooting_systems()
        except Exception as e:
            logger.error(f"Error getting available systems: {str(e)}")
            return []

    def get_symptoms(self, system_id: str) -> List[Dict[str, Any]]:
        """
        Get symptoms for a specific aircraft system.

        Args:
            system_id: System ID

        Returns:
            List[Dict[str, Any]]: List of symptoms for the system
        """
        try:
            system_data = self.mock_service.get_troubleshooting_symptoms(system_id)
            return system_data.get("symptoms", [])
        except Exception as e:
            logger.error(f"Error getting symptoms for system {system_id}: {str(e)}")
            return []

    def diagnose_issue(
        self,
        system: str,
        symptoms: List[str],
        context: Optional[str] = None,
        maintenance_history: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Diagnose an issue based on system and symptoms.

        Args:
            system: System ID
            symptoms: List of symptom IDs
            context: Optional context information
            maintenance_history: Optional maintenance history data

        Returns:
            Dict[str, Any]: Diagnosis result with potential causes and solutions
        """
        try:
            # Create request object
            request = {
                "system": system,
                "symptoms": symptoms,
                "context": context or ""
            }

            # Get analysis from mock data service
            analysis_data = self.mock_service.analyze_troubleshooting(request)

            # If maintenance history is provided, adjust cause probabilities
            if maintenance_history:
                analysis_data = self._adjust_with_maintenance_history(analysis_data, maintenance_history)

            return analysis_data
        except Exception as e:
            logger.error(f"Error diagnosing issue: {str(e)}")
            # Return a basic response structure in case of error
            return {
                "request": {
                    "system": system,
                    "symptoms": symptoms,
                    "context": context or ""
                },
                "analysis": {
                    "potential_causes": [],
                    "recommended_solutions": [],
                    "additional_resources": []
                }
            }

    def _adjust_with_maintenance_history(
        self,
        analysis_data: Dict[str, Any],
        maintenance_history: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adjust diagnosis based on maintenance history.

        Args:
            analysis_data: Original analysis data
            maintenance_history: Maintenance history data

        Returns:
            Dict[str, Any]: Adjusted analysis data
        """
        # Create a copy of the analysis data to avoid modifying the original
        adjusted_data = json.loads(json.dumps(analysis_data))

        try:
            # Get potential causes from the analysis
            potential_causes = adjusted_data.get("analysis", {}).get("potential_causes", [])

            # Get recent maintenance events
            recent_events = maintenance_history.get("recent_events", [])

            # Adjust probabilities based on maintenance history
            for cause in potential_causes:
                cause_id = cause.get("id", "")
                cause_desc = cause.get("description", "").lower()

                # Check for related maintenance events
                for event in recent_events:
                    event_desc = event.get("description", "").lower()
                    event_type = event.get("type", "").lower()

                    # If there was a recent repair related to this cause, reduce probability
                    if any(keyword in event_desc for keyword in cause_desc.split()):
                        if event_type == "repair" or event_type == "replacement":
                            cause["probability"] = max(0.1, cause["probability"] - 0.3)
                            cause["evidence"] += f" However, there was a recent {event_type} that addressed this issue."

                    # If there was a recent inspection with no issues found, reduce probability
                    elif event_type == "inspection" and "no issues found" in event_desc:
                        cause["probability"] = max(0.1, cause["probability"] - 0.2)
                        cause["evidence"] += " A recent inspection found no issues with this component."

                    # If there was a recent issue reported but not fixed, increase probability
                    elif event_type == "issue_reported" and any(keyword in event_desc for keyword in cause_desc.split()):
                        cause["probability"] = min(0.95, cause["probability"] + 0.2)
                        cause["evidence"] += " This aligns with a recently reported issue that hasn't been addressed yet."

            # Re-sort causes by probability
            adjusted_data["analysis"]["potential_causes"] = sorted(
                potential_causes,
                key=lambda x: x.get("probability", 0),
                reverse=True
            )

            return adjusted_data
        except Exception as e:
            logger.error(f"Error adjusting with maintenance history: {str(e)}")
            return analysis_data

    def generate_troubleshooting_procedure(
        self,
        system_id: str,
        cause_id: str,
        aircraft_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a detailed troubleshooting procedure for a specific cause.

        Args:
            system_id: System ID
            cause_id: Cause ID
            aircraft_type: Optional aircraft type for customization

        Returns:
            Dict[str, Any]: Detailed troubleshooting procedure
        """
        try:
            # Get analysis data for the system
            request = {
                "system": system_id,
                "symptoms": [],  # Empty for now, we just need the system analysis
                "context": ""
            }

            analysis_data = self.mock_service.analyze_troubleshooting(request)

            # Find the recommended solution for the cause
            solutions = analysis_data.get("analysis", {}).get("recommended_solutions", [])

            # Find the solution that best addresses the cause
            # In a real implementation, this would be more sophisticated
            selected_solution = None
            for solution in solutions:
                # For now, just return the first solution
                # In a real implementation, we would match solutions to causes
                selected_solution = solution
                break

            if not selected_solution:
                return {
                    "error": "No solution found for the specified cause"
                }

            # Get parts and tools required for the solution
            parts_and_tools = self._get_parts_and_tools(system_id, selected_solution.get("id", ""))

            # Create the procedure
            procedure = {
                "system_id": system_id,
                "cause_id": cause_id,
                "solution": selected_solution,
                "parts_and_tools": parts_and_tools,
                "safety_precautions": self._get_safety_precautions(system_id),
                "estimated_time": selected_solution.get("estimated_time", "Unknown"),
                "difficulty": selected_solution.get("difficulty", "medium")
            }

            return procedure
        except Exception as e:
            logger.error(f"Error generating troubleshooting procedure: {str(e)}")
            return {
                "error": f"Error generating troubleshooting procedure: {str(e)}"
            }

    def _get_parts_and_tools(self, system_id: str, solution_id: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Get parts and tools required for a solution.

        Args:
            system_id: System ID
            solution_id: Solution ID

        Returns:
            Dict[str, List[Dict[str, str]]]: Parts and tools required
        """
        # In a real implementation, this would query a parts and tools database
        # For now, return mock data
        return {
            "parts": [
                {
                    "id": "part-001",
                    "name": "Hydraulic Pump",
                    "part_number": "HP-123-456",
                    "quantity": "1"
                },
                {
                    "id": "part-002",
                    "name": "O-Ring Seal",
                    "part_number": "OR-789-012",
                    "quantity": "2"
                }
            ],
            "tools": [
                {
                    "id": "tool-001",
                    "name": "Hydraulic Pressure Gauge",
                    "tool_number": "HPG-345-678"
                },
                {
                    "id": "tool-002",
                    "name": "Torque Wrench",
                    "tool_number": "TW-901-234"
                }
            ]
        }

    def _get_safety_precautions(self, system_id: str) -> List[str]:
        """
        Get safety precautions for a system.

        Args:
            system_id: System ID

        Returns:
            List[str]: Safety precautions
        """
        # In a real implementation, this would query a safety database
        # For now, return mock data based on system ID
        common_precautions = [
            "Ensure aircraft is properly grounded before beginning work",
            "Wear appropriate personal protective equipment (PPE)",
            "Follow all standard safety procedures in the maintenance manual"
        ]

        system_specific_precautions = {
            "sys-001": [  # Hydraulic System
                "Relieve all hydraulic pressure before disconnecting lines",
                "Use caution when handling hydraulic fluid - it may be hot",
                "Clean up any hydraulic fluid spills immediately to prevent slip hazards"
            ],
            "sys-002": [  # Electrical System
                "Disconnect battery and external power before working on electrical components",
                "Use insulated tools when working with electrical systems",
                "Verify absence of voltage before touching electrical components"
            ],
            "sys-003": [  # Avionics System
                "Use anti-static wrist straps when handling avionics components",
                "Protect avionics components from moisture and contaminants",
                "Avoid using magnetic tools near sensitive avionics equipment"
            ],
            "sys-004": [  # Landing Gear System
                "Use proper landing gear safety pins before working on landing gear",
                "Never position yourself under unsecured landing gear components",
                "Be aware of stored energy in struts and actuators"
            ],
            "sys-005": [  # Fuel System
                "Ensure adequate ventilation when working with fuel systems",
                "No smoking or open flames in the work area",
                "Have fire extinguishing equipment readily available"
            ]
        }

        # Return common precautions plus system-specific ones
        return common_precautions + system_specific_precautions.get(system_id, [])


# Create a singleton instance for use throughout the application
troubleshooting_service = TroubleshootingService()
