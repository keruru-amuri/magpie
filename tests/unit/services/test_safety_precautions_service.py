"""
Unit tests for the SafetyPrecautionsService.
"""
import pytest
from unittest.mock import patch, MagicMock
import os
import json

from app.services.safety_precautions_service import SafetyPrecautionsService


class TestSafetyPrecautionsService:
    """Tests for the SafetyPrecautionsService."""

    @pytest.fixture
    def mock_safety_precautions(self):
        """Mock safety precautions data."""
        return [
            {
                "id": "sp-001",
                "type": "precaution",
                "severity": "medium",
                "description": "Ensure aircraft is properly grounded before beginning work",
                "hazard_level": "caution",
                "display_location": "before_procedure",
                "applicable_systems": ["all"],
                "applicable_procedure_types": ["all"],
                "applicable_aircraft_types": ["all"]
            },
            {
                "id": "sp-002",
                "type": "warning",
                "severity": "high",
                "description": "Ensure all power is disconnected before working on electrical components",
                "hazard_level": "warning",
                "display_location": "before_procedure",
                "applicable_systems": ["electrical", "avionics"],
                "applicable_procedure_types": ["all"],
                "applicable_aircraft_types": ["all"]
            },
            {
                "id": "sp-003",
                "type": "caution",
                "severity": "medium",
                "description": "Use anti-static wrist straps when handling avionics components",
                "hazard_level": "caution",
                "display_location": "before_procedure",
                "applicable_systems": ["avionics", "electrical"],
                "applicable_procedure_types": ["all"],
                "applicable_aircraft_types": ["all"]
            }
        ]

    @pytest.fixture
    def mock_procedure_safety_mappings(self):
        """Mock procedure safety mappings data."""
        return {
            "inspection": {
                "general": {
                    "before_procedure": ["sp-001"],
                    "during_procedure": [],
                    "after_procedure": [],
                    "specific_steps": {
                        "preparation": ["sp-012"]
                    }
                },
                "electrical": {
                    "before_procedure": ["sp-001", "sp-002"],
                    "during_procedure": [],
                    "after_procedure": [],
                    "specific_steps": {}
                },
                "avionics": {
                    "before_procedure": ["sp-001", "sp-002", "sp-003"],
                    "during_procedure": [],
                    "after_procedure": [],
                    "specific_steps": {}
                }
            }
        }

    @pytest.fixture
    def mock_service(self, mock_safety_precautions, mock_procedure_safety_mappings):
        """Create a mock SafetyPrecautionsService."""
        with patch("app.services.safety_precautions_service.os.path.exists", return_value=True), \
             patch("builtins.open", MagicMock()), \
             patch("json.load") as mock_json_load:
            
            # Configure mock_json_load to return different values based on the file being loaded
            def side_effect(file_handle):
                mock_file_path = file_handle.name
                if "common_precautions.json" in mock_file_path:
                    return mock_safety_precautions
                elif "procedure_safety_mappings.json" in mock_file_path:
                    return mock_procedure_safety_mappings
                return {}
            
            mock_json_load.side_effect = side_effect
            
            service = SafetyPrecautionsService()
            
            # Manually set the data
            service.safety_precautions = {p["id"]: p for p in mock_safety_precautions}
            service.procedure_safety_mappings = mock_procedure_safety_mappings
            
            return service

    def test_init_and_load_data(self, mock_service):
        """Test initialization and data loading."""
        assert len(mock_service.safety_precautions) == 3
        assert "sp-001" in mock_service.safety_precautions
        assert "sp-002" in mock_service.safety_precautions
        assert "sp-003" in mock_service.safety_precautions
        assert "inspection" in mock_service.procedure_safety_mappings

    def test_get_all_safety_precautions(self, mock_service):
        """Test getting all safety precautions."""
        precautions = mock_service.get_all_safety_precautions()
        assert len(precautions) == 3
        assert any(p["id"] == "sp-001" for p in precautions)
        assert any(p["id"] == "sp-002" for p in precautions)
        assert any(p["id"] == "sp-003" for p in precautions)

    def test_get_safety_precaution(self, mock_service):
        """Test getting a specific safety precaution."""
        precaution = mock_service.get_safety_precaution("sp-002")
        assert precaution is not None
        assert precaution["id"] == "sp-002"
        assert precaution["type"] == "warning"
        assert precaution["severity"] == "high"
        assert precaution["hazard_level"] == "warning"

    def test_get_safety_precautions_by_type(self, mock_service):
        """Test getting safety precautions by type."""
        precautions = mock_service.get_safety_precautions_by_type("warning")
        assert len(precautions) == 1
        assert precautions[0]["id"] == "sp-002"
        assert precautions[0]["type"] == "warning"

    def test_get_safety_precautions_by_severity(self, mock_service):
        """Test getting safety precautions by severity."""
        precautions = mock_service.get_safety_precautions_by_severity("high")
        assert len(precautions) == 1
        assert precautions[0]["id"] == "sp-002"
        assert precautions[0]["severity"] == "high"

    def test_get_safety_precautions_by_hazard_level(self, mock_service):
        """Test getting safety precautions by hazard level."""
        precautions = mock_service.get_safety_precautions_by_hazard_level("warning")
        assert len(precautions) == 1
        assert precautions[0]["id"] == "sp-002"
        assert precautions[0]["hazard_level"] == "warning"

    def test_get_safety_precautions_for_procedure(self, mock_service):
        """Test getting safety precautions for a procedure."""
        precautions = mock_service.get_safety_precautions_for_procedure(
            procedure_type="inspection",
            system="electrical"
        )
        assert len(precautions) == 2
        assert any(p["id"] == "sp-001" for p in precautions)
        assert any(p["id"] == "sp-002" for p in precautions)

    def test_get_safety_precautions_for_procedure_with_display_location(self, mock_service):
        """Test getting safety precautions for a procedure with display location."""
        precautions = mock_service.get_safety_precautions_for_procedure(
            procedure_type="inspection",
            system="electrical",
            display_location="before_procedure"
        )
        assert len(precautions) == 2
        assert any(p["id"] == "sp-001" for p in precautions)
        assert any(p["id"] == "sp-002" for p in precautions)

    def test_extract_safety_precautions_from_text(self, mock_service):
        """Test extracting safety precautions from text."""
        text = "Make sure to ensure all power is disconnected before working on electrical components."
        precautions = mock_service.extract_safety_precautions_from_text(text)
        assert len(precautions) == 1
        assert precautions[0]["id"] == "sp-002"

    def test_extract_safety_precautions_from_procedure(self, mock_service):
        """Test extracting safety precautions from a procedure."""
        procedure = {
            "description": "This procedure involves working with electrical components.",
            "steps": [
                {
                    "title": "Preparation",
                    "description": "Ensure aircraft is properly grounded before beginning work.",
                    "cautions": ["Use anti-static wrist straps when handling avionics components."]
                }
            ]
        }
        precautions = mock_service.extract_safety_precautions_from_procedure(procedure)
        assert len(precautions) == 2
        assert any(p["id"] == "sp-001" for p in precautions)
        assert any(p["id"] == "sp-003" for p in precautions)

    def test_enrich_procedure_with_safety_precautions(self, mock_service):
        """Test enriching a procedure with safety precautions."""
        procedure = {
            "title": "Electrical System Inspection",
            "description": "Inspection procedure for aircraft electrical system.",
            "steps": [
                {
                    "title": "Preparation",
                    "description": "Prepare for inspection.",
                    "cautions": []
                }
            ]
        }
        enriched = mock_service.enrich_procedure_with_safety_precautions(
            procedure=procedure,
            procedure_type="inspection",
            system="electrical"
        )
        assert "safety_precautions" in enriched
        assert len(enriched["safety_precautions"]) == 2
        assert any(p == "Ensure aircraft is properly grounded before beginning work" for p in enriched["safety_precautions"])
        assert any(p == "Ensure all power is disconnected before working on electrical components" for p in enriched["safety_precautions"])

    def test_validate_procedure_safety_precautions(self, mock_service):
        """Test validating safety precautions in a procedure."""
        procedure = {
            "title": "Electrical System Inspection",
            "description": "Inspection procedure for aircraft electrical system.",
            "safety_precautions": [
                "Ensure aircraft is properly grounded before beginning work"
            ],
            "steps": [
                {
                    "title": "Preparation",
                    "description": "Prepare for inspection.",
                    "cautions": []
                }
            ]
        }
        validation = mock_service.validate_procedure_safety_precautions(
            procedure=procedure,
            procedure_type="inspection",
            system="electrical"
        )
        assert not validation["valid"]
        assert len(validation["missing_precautions"]) == 1
        assert validation["missing_precautions"][0] == "Ensure all power is disconnected before working on electrical components"

    def test_format_safety_precautions_as_markdown(self, mock_service):
        """Test formatting safety precautions as Markdown."""
        precautions = mock_service.get_all_safety_precautions()
        markdown = mock_service.format_safety_precautions_as_markdown(precautions)
        assert "# Safety Precautions" in markdown
        assert "## Warning" in markdown
        assert "## Caution" in markdown
        assert "- **Ensure all power is disconnected before working on electrical components**" in markdown
        assert "- Ensure aircraft is properly grounded before beginning work" in markdown
        assert "- Use anti-static wrist straps when handling avionics components" in markdown
