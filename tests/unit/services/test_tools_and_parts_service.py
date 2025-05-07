"""
Unit tests for the ToolsAndPartsService.
"""
import json
import os
import pytest
from unittest.mock import patch, MagicMock

from app.services.tools_and_parts_service import ToolsAndPartsService


@pytest.fixture
def mock_tools_data():
    return [
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
    ]


@pytest.fixture
def mock_parts_data():
    return [
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
    ]


@pytest.fixture
def mock_equipment_data():
    return [
        {
            "id": "equip-001",
            "name": "Aircraft Jack",
            "category": "Ground Support Equipment",
            "description": "Hydraulic jack for lifting aircraft during maintenance"
        },
        {
            "id": "equip-002",
            "name": "Nitrogen Service Cart",
            "category": "Ground Support Equipment",
            "description": "Mobile cart for servicing aircraft nitrogen systems"
        }
    ]


@pytest.fixture
def mock_aircraft_tool_mappings():
    return {
        "Boeing 737": {
            "hydraulic": ["tool-001", "tool-002"],
            "electrical": ["tool-001", "tool-002"],
            "specialized": [
                {
                    "id": "spec-b737-001",
                    "name": "737 Flap Rigging Tool",
                    "description": "Specialized tool for rigging 737 flaps",
                    "procedures": ["flap_rigging", "flap_adjustment"]
                }
            ]
        }
    }


@pytest.fixture
def mock_aircraft_part_mappings():
    return {
        "Boeing 737": {
            "hydraulic": ["part-001", "part-002"],
            "electrical": ["part-001"],
            "specialized": [
                {
                    "id": "spec-part-b737-001",
                    "name": "737 Hydraulic Pump",
                    "part_number": "65-20698-1",
                    "description": "Main hydraulic pump for Boeing 737",
                    "procedures": ["hydraulic_pump_replacement"]
                }
            ]
        }
    }


@pytest.fixture
def mock_procedure_resource_mappings():
    return {
        "inspection": {
            "general": {
                "tools": ["tool-001", "tool-002"],
                "parts": [],
                "equipment": []
            },
            "hydraulic": {
                "tools": ["tool-001", "tool-002"],
                "parts": ["part-001", "part-002"],
                "equipment": ["equip-001"]
            }
        }
    }


@pytest.fixture
def mock_procedure():
    return {
        "id": "proc-001",
        "title": "Hydraulic System Inspection",
        "description": "Inspection procedure for aircraft hydraulic system using a torque wrench and socket set.",
        "steps": [
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


class TestToolsAndPartsService:
    """
    Test cases for the ToolsAndPartsService.
    """

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=MagicMock)
    def test_init_and_load_data(self, mock_open, mock_exists, mock_tools_data, mock_parts_data, mock_equipment_data,
                               mock_aircraft_tool_mappings, mock_aircraft_part_mappings, mock_procedure_resource_mappings):
        # Setup mocks
        mock_exists.return_value = True
        mock_file_handles = [
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock()
        ]
        mock_open.side_effect = mock_file_handles

        # Setup mock file content
        mock_file_handles[0].__enter__.return_value.read.return_value = json.dumps(mock_tools_data)
        mock_file_handles[1].__enter__.return_value.read.return_value = json.dumps(mock_parts_data)
        mock_file_handles[2].__enter__.return_value.read.return_value = json.dumps(mock_equipment_data)
        mock_file_handles[3].__enter__.return_value.read.return_value = json.dumps(mock_aircraft_tool_mappings)
        mock_file_handles[4].__enter__.return_value.read.return_value = json.dumps(mock_aircraft_part_mappings)
        mock_file_handles[5].__enter__.return_value.read.return_value = json.dumps(mock_procedure_resource_mappings)

        # Initialize service
        service = ToolsAndPartsService()

        # Verify data was loaded
        assert len(service.tools) == 2
        assert len(service.parts) == 2
        assert len(service.equipment) == 2
        assert "Boeing 737" in service.aircraft_tool_mappings
        assert "Boeing 737" in service.aircraft_part_mappings
        assert "inspection" in service.procedure_resource_mappings

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=MagicMock)
    def test_get_all_tools(self, mock_open, mock_exists, mock_tools_data):
        # Setup mocks
        mock_exists.return_value = True
        mock_file_handle = MagicMock()
        mock_open.return_value = mock_file_handle
        mock_file_handle.__enter__.return_value.read.return_value = json.dumps(mock_tools_data)

        # Initialize service with mocked data
        service = ToolsAndPartsService()
        service.tools = {tool["id"]: tool for tool in mock_tools_data}

        # Test get_all_tools
        tools = service.get_all_tools()

        # Verify results
        assert len(tools) == 2
        assert tools[0]["id"] in ["tool-001", "tool-002"]
        assert tools[1]["id"] in ["tool-001", "tool-002"]

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=MagicMock)
    def test_get_tool(self, mock_open, mock_exists, mock_tools_data):
        # Setup mocks
        mock_exists.return_value = True
        mock_file_handle = MagicMock()
        mock_open.return_value = mock_file_handle
        mock_file_handle.__enter__.return_value.read.return_value = json.dumps(mock_tools_data)

        # Initialize service with mocked data
        service = ToolsAndPartsService()
        service.tools = {tool["id"]: tool for tool in mock_tools_data}

        # Test get_tool
        tool = service.get_tool("tool-001")

        # Verify results
        assert tool is not None
        assert tool["id"] == "tool-001"
        assert tool["name"] == "Socket Set"

        # Test get_tool with non-existent ID
        tool = service.get_tool("non-existent")
        assert tool is None

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=MagicMock)
    def test_get_tools_by_category(self, mock_open, mock_exists, mock_tools_data):
        # Setup mocks
        mock_exists.return_value = True
        mock_file_handle = MagicMock()
        mock_open.return_value = mock_file_handle
        mock_file_handle.__enter__.return_value.read.return_value = json.dumps(mock_tools_data)

        # Initialize service with mocked data
        service = ToolsAndPartsService()
        service.tools = {tool["id"]: tool for tool in mock_tools_data}

        # Test get_tools_by_category
        tools = service.get_tools_by_category("Hand Tool")

        # Verify results
        assert len(tools) == 2
        assert tools[0]["category"] == "Hand Tool"
        assert tools[1]["category"] == "Hand Tool"

        # Test with non-existent category
        tools = service.get_tools_by_category("Non-existent")
        assert len(tools) == 0

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=MagicMock)
    def test_get_tools_for_aircraft_system(self, mock_open, mock_exists, mock_tools_data, mock_aircraft_tool_mappings):
        # Setup mocks
        mock_exists.return_value = True
        mock_file_handle = MagicMock()
        mock_open.return_value = mock_file_handle
        mock_file_handle.__enter__.return_value.read.return_value = json.dumps(mock_tools_data)

        # Initialize service with mocked data
        service = ToolsAndPartsService()
        service.tools = {tool["id"]: tool for tool in mock_tools_data}
        service.aircraft_tool_mappings = mock_aircraft_tool_mappings

        # Test get_tools_for_aircraft_system
        tools = service.get_tools_for_aircraft_system("Boeing 737", "hydraulic")

        # Verify results
        assert len(tools) == 3  # 2 regular tools + 1 specialized tool
        assert any(tool["id"] == "tool-001" for tool in tools)
        assert any(tool["id"] == "tool-002" for tool in tools)
        assert any(tool["id"] == "spec-b737-001" for tool in tools)

        # Test with specialized tools
        tools = service.get_tools_for_aircraft_system("Boeing 737", "flap")

        # Verify specialized tools are included
        specialized_tools = [tool for tool in tools if tool["id"].startswith("spec-")]
        assert len(specialized_tools) > 0
        assert specialized_tools[0]["id"] == "spec-b737-001"

        # Test with non-existent aircraft
        tools = service.get_tools_for_aircraft_system("Non-existent", "hydraulic")
        assert len(tools) == 0

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=MagicMock)
    def test_get_resources_for_procedure(self, mock_open, mock_exists, mock_tools_data, mock_parts_data,
                                        mock_equipment_data, mock_procedure_resource_mappings):
        # Setup mocks
        mock_exists.return_value = True
        mock_file_handle = MagicMock()
        mock_open.return_value = mock_file_handle
        mock_file_handle.__enter__.return_value.read.return_value = json.dumps(mock_tools_data)

        # Initialize service with mocked data
        service = ToolsAndPartsService()
        service.tools = {tool["id"]: tool for tool in mock_tools_data}
        service.parts = {part["id"]: part for part in mock_parts_data}
        service.equipment = {equip["id"]: equip for equip in mock_equipment_data}
        service.procedure_resource_mappings = mock_procedure_resource_mappings

        # Test get_resources_for_procedure
        resources = service.get_resources_for_procedure("inspection", "hydraulic")

        # Verify results
        assert "tools" in resources
        assert "parts" in resources
        assert "equipment" in resources
        assert len(resources["tools"]) == 2
        assert len(resources["parts"]) == 2
        assert len(resources["equipment"]) == 1

        # Test with non-existent procedure type
        resources = service.get_resources_for_procedure("non-existent", "hydraulic")
        assert len(resources["tools"]) == 0
        assert len(resources["parts"]) == 0
        assert len(resources["equipment"]) == 0

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=MagicMock)
    def test_extract_tools_from_text(self, mock_open, mock_exists, mock_tools_data):
        # Setup mocks
        mock_exists.return_value = True
        mock_file_handle = MagicMock()
        mock_open.return_value = mock_file_handle
        mock_file_handle.__enter__.return_value.read.return_value = json.dumps(mock_tools_data)

        # Initialize service with mocked data
        service = ToolsAndPartsService()
        service.tools = {tool["id"]: tool for tool in mock_tools_data}

        # Test extract_tools_from_text
        text = "Use a socket set and torque wrench to tighten the bolts."
        tools = service.extract_tools_from_text(text)

        # Verify results
        assert len(tools) == 2
        assert tools[0]["name"] in ["Socket Set", "Torque Wrench"]
        assert tools[1]["name"] in ["Socket Set", "Torque Wrench"]

        # Test with text that doesn't mention tools
        text = "Perform a visual inspection of the component."
        tools = service.extract_tools_from_text(text)
        assert len(tools) == 0

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=MagicMock)
    def test_extract_resources_from_procedure(self, mock_open, mock_exists, mock_tools_data,
                                             mock_parts_data, mock_equipment_data, mock_procedure):
        # Setup mocks
        mock_exists.return_value = True
        mock_file_handle = MagicMock()
        mock_open.return_value = mock_file_handle
        mock_file_handle.__enter__.return_value.read.return_value = json.dumps(mock_tools_data)

        # Initialize service with mocked data
        service = ToolsAndPartsService()
        service.tools = {tool["id"]: tool for tool in mock_tools_data}
        service.parts = {part["id"]: part for part in mock_parts_data}
        service.equipment = {equip["id"]: equip for equip in mock_equipment_data}

        # Test extract_resources_from_procedure
        resources = service.extract_resources_from_procedure(mock_procedure)

        # Verify results
        assert "tools" in resources
        assert "parts" in resources
        assert "equipment" in resources
        assert len(resources["tools"]) == 2  # Socket Set and Torque Wrench
        assert len(resources["parts"]) == 1  # Hydraulic Fluid
        assert len(resources["equipment"]) == 0

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=MagicMock)
    def test_generate_consolidated_resource_list(self, mock_open, mock_exists, mock_tools_data,
                                               mock_parts_data, mock_equipment_data,
                                               mock_procedure_resource_mappings, mock_procedure):
        # Setup mocks
        mock_exists.return_value = True
        mock_file_handle = MagicMock()
        mock_open.return_value = mock_file_handle
        mock_file_handle.__enter__.return_value.read.return_value = json.dumps(mock_tools_data)

        # Initialize service with mocked data
        service = ToolsAndPartsService()
        service.tools = {tool["id"]: tool for tool in mock_tools_data}
        service.parts = {part["id"]: part for part in mock_parts_data}
        service.equipment = {equip["id"]: equip for equip in mock_equipment_data}
        service.procedure_resource_mappings = mock_procedure_resource_mappings

        # Test generate_consolidated_resource_list with JSON format
        resources = service.generate_consolidated_resource_list(
            procedure=mock_procedure,
            procedure_type="inspection",
            system="hydraulic",
            format="json"
        )

        # Verify JSON results
        assert "tools" in resources
        assert "parts" in resources
        assert "equipment" in resources
        assert len(resources["tools"]) >= 2
        assert len(resources["parts"]) >= 1

        # Test generate_consolidated_resource_list with Markdown format
        markdown = service.generate_consolidated_resource_list(
            procedure=mock_procedure,
            procedure_type="inspection",
            system="hydraulic",
            format="markdown"
        )

        # Verify Markdown results
        assert isinstance(markdown, str)
        assert "# Required Resources" in markdown
        assert "## Tools" in markdown
        assert "## Parts" in markdown
        assert "## Equipment" in markdown
        assert "Socket Set" in markdown
        assert "Torque Wrench" in markdown
        assert "Hydraulic Fluid" in markdown
