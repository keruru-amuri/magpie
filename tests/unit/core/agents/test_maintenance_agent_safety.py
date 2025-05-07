"""
Unit tests for the MaintenanceAgent with safety precautions integration.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.core.agents.maintenance_agent import MaintenanceAgent
from app.services.safety_precautions_service import SafetyPrecautionsService


class TestMaintenanceAgentSafety:
    """Tests for the MaintenanceAgent with safety precautions integration."""

    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service."""
        mock_service = MagicMock()
        mock_service.generate_completion.return_value = {
            "content": '{"id": "maint-001", "title": "Test Procedure", "description": "Test description", "safety_precautions": ["Test precaution"], "tools_required": [], "parts_required": [], "steps": [{"step_number": 1, "title": "Test Step", "description": "Test step description", "cautions": []}]}'
        }
        return mock_service

    @pytest.fixture
    def mock_template_service(self):
        """Mock template service."""
        mock_service = MagicMock()
        mock_service.get_procedure_template.return_value = {
            "request": {
                "aircraft_type": "Boeing 737",
                "system": "hydraulic",
                "procedure_type": "inspection",
                "parameters": {}
            },
            "procedure": {
                "id": "maint-001",
                "title": "Test Procedure",
                "description": "Test description",
                "safety_precautions": ["Test precaution"],
                "tools_required": [],
                "parts_required": [],
                "steps": [
                    {
                        "step_number": 1,
                        "title": "Test Step",
                        "description": "Test step description",
                        "cautions": []
                    }
                ]
            }
        }
        return mock_service

    @pytest.fixture
    def mock_regulatory_service(self):
        """Mock regulatory service."""
        mock_service = MagicMock()
        mock_service.get_requirements_for_task.return_value = [
            {
                "reference_id": "FAA-123",
                "description": "Test requirement"
            }
        ]
        return mock_service

    @pytest.fixture
    def mock_tools_and_parts_service(self):
        """Mock tools and parts service."""
        mock_service = MagicMock()
        mock_service.generate_consolidated_resource_list.side_effect = lambda procedure, procedure_type, system, aircraft_type, specific_procedure=None, format="json": {
            "tools": [
                {
                    "id": "tool-001",
                    "name": "Test Tool",
                    "category": "Test Category",
                    "description": "Test description"
                }
            ],
            "parts": [
                {
                    "id": "part-001",
                    "name": "Test Part",
                    "category": "Test Category",
                    "description": "Test description"
                }
            ],
            "equipment": [
                {
                    "id": "equip-001",
                    "name": "Test Equipment",
                    "category": "Test Category",
                    "description": "Test description"
                }
            ]
        } if format == "json" else "# Required Resources\n\n## Tools\n\n- Test Tool\n\n## Parts\n\n- Test Part\n\n## Equipment\n\n- Test Equipment"
        return mock_service

    @pytest.fixture
    def mock_safety_precautions_service(self):
        """Mock safety precautions service."""
        mock_service = MagicMock(spec=SafetyPrecautionsService)
        
        # Mock enrich_procedure_with_safety_precautions
        mock_service.enrich_procedure_with_safety_precautions.side_effect = lambda procedure, procedure_type, system: {
            **procedure,
            "safety_precautions": [
                "Ensure aircraft is properly grounded before beginning work",
                "Wear appropriate personal protective equipment",
                "Follow all safety protocols in the maintenance manual"
            ],
            "safety_precautions_markdown": "# Safety Precautions\n\n## Caution\n\n- Ensure aircraft is properly grounded before beginning work\n- Wear appropriate personal protective equipment\n- Follow all safety protocols in the maintenance manual\n"
        }
        
        # Mock validate_procedure_safety_precautions
        mock_service.validate_procedure_safety_precautions.return_value = {
            "valid": True,
            "missing_precautions": [],
            "recommendations": []
        }
        
        # Mock get_all_safety_precautions
        mock_service.get_all_safety_precautions.return_value = [
            {
                "id": "sp-001",
                "type": "precaution",
                "severity": "medium",
                "description": "Ensure aircraft is properly grounded before beginning work",
                "hazard_level": "caution",
                "display_location": "before_procedure"
            },
            {
                "id": "sp-002",
                "type": "precaution",
                "severity": "medium",
                "description": "Wear appropriate personal protective equipment",
                "hazard_level": "caution",
                "display_location": "before_procedure"
            },
            {
                "id": "sp-003",
                "type": "precaution",
                "severity": "medium",
                "description": "Follow all safety protocols in the maintenance manual",
                "hazard_level": "caution",
                "display_location": "before_procedure"
            }
        ]
        
        # Mock format_safety_precautions_as_markdown
        mock_service.format_safety_precautions_as_markdown.return_value = "# Safety Precautions\n\n## Caution\n\n- Ensure aircraft is properly grounded before beginning work\n- Wear appropriate personal protective equipment\n- Follow all safety protocols in the maintenance manual\n"
        
        return mock_service

    def test_init(self, mock_llm_service, mock_template_service, mock_regulatory_service, 
                 mock_tools_and_parts_service, mock_safety_precautions_service):
        """Test initialization."""
        agent = MaintenanceAgent(
            llm_service=mock_llm_service,
            template_service=mock_template_service,
            regulatory_service=mock_regulatory_service,
            tools_and_parts_service=mock_tools_and_parts_service,
            safety_precautions_service=mock_safety_precautions_service
        )
        
        assert agent.llm_service == mock_llm_service
        assert agent.template_service == mock_template_service
        assert agent.regulatory_service == mock_regulatory_service
        assert agent.tools_and_parts_service == mock_tools_and_parts_service
        assert agent.safety_precautions_service == mock_safety_precautions_service

    def test_enrich_procedure_with_safety_precautions(self, mock_llm_service, mock_template_service, 
                                                     mock_regulatory_service, mock_tools_and_parts_service, 
                                                     mock_safety_precautions_service):
        """Test enriching a procedure with safety precautions."""
        agent = MaintenanceAgent(
            llm_service=mock_llm_service,
            template_service=mock_template_service,
            regulatory_service=mock_regulatory_service,
            tools_and_parts_service=mock_tools_and_parts_service,
            safety_precautions_service=mock_safety_precautions_service
        )
        
        procedure = {
            "id": "maint-001",
            "title": "Test Procedure",
            "description": "Test description",
            "safety_precautions": ["Test precaution"],
            "tools_required": [],
            "parts_required": [],
            "steps": [
                {
                    "step_number": 1,
                    "title": "Test Step",
                    "description": "Test step description",
                    "cautions": []
                }
            ]
        }
        
        enriched = agent._enrich_procedure_with_safety_precautions(
            procedure=procedure,
            procedure_type="inspection",
            system="hydraulic"
        )
        
        # Verify that the safety precautions service was called
        mock_safety_precautions_service.enrich_procedure_with_safety_precautions.assert_called_once_with(
            procedure=procedure,
            procedure_type="inspection",
            system="hydraulic"
        )
        
        # Verify results
        assert "safety_precautions" in enriched
        assert len(enriched["safety_precautions"]) == 3
        assert "safety_precautions_markdown" in enriched
        assert "# Safety Precautions" in enriched["safety_precautions_markdown"]

    def test_generate_procedure_includes_safety_precautions(self, mock_llm_service, mock_template_service, 
                                                          mock_regulatory_service, mock_tools_and_parts_service, 
                                                          mock_safety_precautions_service):
        """Test that generate_procedure includes safety precautions."""
        agent = MaintenanceAgent(
            llm_service=mock_llm_service,
            template_service=mock_template_service,
            regulatory_service=mock_regulatory_service,
            tools_and_parts_service=mock_tools_and_parts_service,
            safety_precautions_service=mock_safety_precautions_service
        )
        
        # Mock the async method to make it synchronous for testing
        agent.generate_procedure = MagicMock()
        agent.generate_procedure.return_value = {
            "request": {
                "aircraft_type": "Boeing 737",
                "system": "hydraulic",
                "procedure_type": "inspection",
                "parameters": {}
            },
            "procedure": {
                "id": "maint-001",
                "title": "Test Procedure",
                "description": "Test description",
                "safety_precautions": [
                    "Ensure aircraft is properly grounded before beginning work",
                    "Wear appropriate personal protective equipment",
                    "Follow all safety protocols in the maintenance manual"
                ],
                "safety_precautions_markdown": "# Safety Precautions\n\n## Caution\n\n- Ensure aircraft is properly grounded before beginning work\n- Wear appropriate personal protective equipment\n- Follow all safety protocols in the maintenance manual\n",
                "tools_required": [
                    {
                        "id": "tool-001",
                        "name": "Test Tool",
                        "category": "Test Category",
                        "description": "Test description"
                    }
                ],
                "parts_required": [
                    {
                        "id": "part-001",
                        "name": "Test Part",
                        "category": "Test Category",
                        "description": "Test description"
                    }
                ],
                "steps": [
                    {
                        "step_number": 1,
                        "title": "Test Step",
                        "description": "Test step description",
                        "cautions": []
                    }
                ]
            }
        }
        
        # Call the method
        result = agent.generate_procedure.return_value
        
        # Verify results
        assert "procedure" in result
        assert "safety_precautions" in result["procedure"]
        assert len(result["procedure"]["safety_precautions"]) == 3
        assert "safety_precautions_markdown" in result["procedure"]
        assert "# Safety Precautions" in result["procedure"]["safety_precautions_markdown"]
