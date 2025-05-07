"""
Unit tests for the MaintenanceAgent with tools and parts integration.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from app.core.agents.maintenance_agent import MaintenanceAgent
from app.services.tools_and_parts_service import ToolsAndPartsService


@pytest.fixture
def mock_llm_service():
    mock_service = MagicMock()
    mock_service.generate_response.return_value = {
        "title": "Hydraulic System Inspection",
        "description": "Inspection procedure for aircraft hydraulic system.",
        "procedure_steps": [
            {
                "step_number": 1,
                "title": "Preparation",
                "description": "Prepare the aircraft for hydraulic system inspection."
            },
            {
                "step_number": 2,
                "title": "Inspect Hydraulic Reservoir",
                "description": "Check hydraulic fluid level and condition. Add hydraulic fluid if necessary."
            }
        ]
    }
    return mock_service


@pytest.fixture
def mock_tools_and_parts_service():
    mock_service = MagicMock(spec=ToolsAndPartsService)

    # Mock generate_consolidated_resource_list for JSON format
    mock_service.generate_consolidated_resource_list.side_effect = lambda procedure, procedure_type, system, aircraft_type, specific_procedure=None, format="json": {
        "tools": [
            {
                "id": "tool-001",
                "name": "Socket Set",
                "category": "Hand Tool",
                "description": "Standard socket set for aircraft maintenance",
                "specifications": {
                    "size": "10-19mm",
                    "material": "Chrome Vanadium Steel"
                }
            },
            {
                "id": "tool-002",
                "name": "Torque Wrench",
                "category": "Hand Tool",
                "description": "Calibrated torque wrench for precise fastener tightening",
                "specifications": {
                    "size": "Various",
                    "material": "Steel",
                    "calibration_required": True,
                    "calibration_interval": "12 months"
                }
            }
        ],
        "parts": [
            {
                "id": "part-001",
                "name": "O-ring",
                "category": "Seals",
                "part_number": "MS29513",
                "description": "Standard O-ring for hydraulic and fuel system sealing"
            },
            {
                "id": "part-002",
                "name": "Hydraulic Fluid",
                "category": "Fluids",
                "part_number": "MIL-PRF-5606",
                "description": "Red mineral oil-based hydraulic fluid for aircraft systems"
            }
        ],
        "equipment": [
            {
                "id": "equip-001",
                "name": "Aircraft Jack",
                "category": "Ground Support Equipment",
                "description": "Hydraulic jack for lifting aircraft during maintenance"
            }
        ]
    } if format == "json" else "# Required Resources\n\n## Tools\n\n### Socket Set\n\n- **Category:** Hand Tool\n\n### Torque Wrench\n\n- **Category:** Hand Tool\n\n## Parts\n\n### O-ring\n\n- **Category:** Seals\n\n### Hydraulic Fluid\n\n- **Category:** Fluids\n\n## Equipment\n\n### Aircraft Jack\n\n- **Category:** Ground Support Equipment\n"

    return mock_service


@pytest.fixture
def mock_template_service():
    mock_service = MagicMock()
    mock_service.get_procedure_template.return_value = None
    return mock_service


@pytest.fixture
def mock_regulatory_service():
    mock_service = MagicMock()
    mock_service.get_regulatory_requirements.return_value = "FAA Regulation 14 CFR Part 43: Maintenance, Preventive Maintenance, Rebuilding, and Alteration"
    return mock_service


class TestMaintenanceAgentTools:
    """
    Test cases for the MaintenanceAgent with tools and parts integration.
    """

    def test_init(self, mock_llm_service, mock_template_service, mock_regulatory_service, mock_tools_and_parts_service):
        # Initialize agent
        agent = MaintenanceAgent(
            llm_service=mock_llm_service,
            template_service=mock_template_service,
            regulatory_service=mock_regulatory_service,
            tools_and_parts_service=mock_tools_and_parts_service
        )

        # Verify initialization
        assert agent.llm_service == mock_llm_service
        assert agent.template_service == mock_template_service
        assert agent.regulatory_service == mock_regulatory_service
        assert agent.tools_and_parts_service == mock_tools_and_parts_service

    def test_enrich_procedure_with_tools_and_parts(self, mock_llm_service, mock_template_service,
                                                 mock_regulatory_service, mock_tools_and_parts_service):
        # Initialize agent
        agent = MaintenanceAgent(
            llm_service=mock_llm_service,
            template_service=mock_template_service,
            regulatory_service=mock_regulatory_service,
            tools_and_parts_service=mock_tools_and_parts_service
        )

        # Create a test procedure
        procedure = {
            "title": "Hydraulic System Inspection",
            "description": "Inspection procedure for aircraft hydraulic system.",
            "procedure_steps": [
                {
                    "step_number": 1,
                    "title": "Preparation",
                    "description": "Prepare the aircraft for hydraulic system inspection."
                },
                {
                    "step_number": 2,
                    "title": "Inspect Hydraulic Reservoir",
                    "description": "Check hydraulic fluid level and condition. Add hydraulic fluid if necessary."
                }
            ]
        }

        # Test _enrich_procedure_with_tools_and_parts
        enriched = agent._enrich_procedure_with_tools_and_parts(
            procedure=procedure,
            procedure_type="inspection",
            system="hydraulic",
            aircraft_type="Boeing 737"
        )

        # Verify results
        assert "tools_required" in enriched
        assert "parts_required" in enriched
        assert "equipment_required" in enriched
        assert "resource_list" in enriched

        assert len(enriched["tools_required"]) == 2
        assert len(enriched["parts_required"]) == 2
        assert len(enriched["equipment_required"]) == 1

        assert enriched["tools_required"][0]["name"] in ["Socket Set", "Torque Wrench"]
        assert enriched["parts_required"][0]["name"] in ["O-ring", "Hydraulic Fluid"]
        assert enriched["equipment_required"][0]["name"] == "Aircraft Jack"

        assert isinstance(enriched["resource_list"], str)
        assert "# Required Resources" in enriched["resource_list"]

    def test_generate_procedure_with_llm_includes_tools_and_parts(self, mock_llm_service, mock_template_service,
                                                               mock_regulatory_service, mock_tools_and_parts_service):
        # Initialize agent
        agent = MaintenanceAgent(
            llm_service=mock_llm_service,
            template_service=mock_template_service,
            regulatory_service=mock_regulatory_service,
            tools_and_parts_service=mock_tools_and_parts_service
        )

        # Mock the async method to make it synchronous for testing
        agent.generate_procedure_with_llm = MagicMock()
        agent.generate_procedure_with_llm.return_value = {
            "title": "Hydraulic System Inspection",
            "description": "Inspection procedure for aircraft hydraulic system.",
            "procedure_steps": [
                {
                    "step_number": 1,
                    "title": "Preparation",
                    "description": "Prepare the aircraft for hydraulic system inspection."
                },
                {
                    "step_number": 2,
                    "title": "Inspect Hydraulic Reservoir",
                    "description": "Check hydraulic fluid level and condition. Add hydraulic fluid if necessary."
                }
            ]
        }

        # Test _enrich_procedure_with_tools_and_parts directly
        procedure = agent.generate_procedure_with_llm.return_value
        result = agent._enrich_procedure_with_tools_and_parts(
            procedure=procedure,
            procedure_type="inspection",
            system="hydraulic",
            aircraft_type="Boeing 737"
        )

        # Verify results
        assert "tools_required" in result
        assert "parts_required" in result
        assert "equipment_required" in result
        assert "resource_list" in result

        assert len(result["tools_required"]) == 2
        assert len(result["parts_required"]) == 2
        assert len(result["equipment_required"]) == 1

        # Verify that the tools_and_parts_service was called
        mock_tools_and_parts_service.generate_consolidated_resource_list.assert_called()

    def test_generate_procedure_template_based_includes_tools_and_parts(self, mock_llm_service, mock_template_service,
                                                                     mock_regulatory_service, mock_tools_and_parts_service):
        # Setup mock template service to return a template
        template_procedure = {
            "request": {
                "aircraft_type": "Boeing 737",
                "system": "hydraulic",
                "procedure_type": "inspection",
                "parameters": {}
            },
            "procedure": {
                "title": "Hydraulic System Inspection",
                "description": "Inspection procedure for aircraft hydraulic system.",
                "procedure_steps": [
                    {
                        "step_number": 1,
                        "title": "Preparation",
                        "description": "Prepare the aircraft for hydraulic system inspection."
                    },
                    {
                        "step_number": 2,
                        "title": "Inspect Hydraulic Reservoir",
                        "description": "Check hydraulic fluid level and condition. Add hydraulic fluid if necessary."
                    }
                ]
            }
        }

        # Initialize agent
        agent = MaintenanceAgent(
            llm_service=mock_llm_service,
            template_service=mock_template_service,
            regulatory_service=mock_regulatory_service,
            tools_and_parts_service=mock_tools_and_parts_service
        )

        # Test _enrich_procedure_with_tools_and_parts directly with the template procedure
        result = agent._enrich_procedure_with_tools_and_parts(
            procedure=template_procedure["procedure"],
            procedure_type="inspection",
            system="hydraulic",
            aircraft_type="Boeing 737"
        )

        # Verify results
        assert "tools_required" in result
        assert "parts_required" in result
        assert "equipment_required" in result
        assert "resource_list" in result

        assert len(result["tools_required"]) == 2
        assert len(result["parts_required"]) == 2
        assert len(result["equipment_required"]) == 1

        # Verify that the tools_and_parts_service was called
        mock_tools_and_parts_service.generate_consolidated_resource_list.assert_called()
