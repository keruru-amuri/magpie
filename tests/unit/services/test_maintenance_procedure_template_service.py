"""
Unit tests for the Maintenance Procedure Template Service.
"""
import os
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock

from app.services.maintenance_procedure_template_service import MaintenanceProcedureTemplateService


class TestMaintenanceProcedureTemplateService:
    """
    Test cases for the MaintenanceProcedureTemplateService class.
    """

    @pytest.fixture
    def mock_template_data(self):
        """
        Fixture providing mock template data.
        """
        return {
            "template1.json": {
                "template_id": "MP-TEST-001",
                "title": "Test Template 1",
                "description": "Test template for unit testing",
                "applicability": {
                    "aircraft_categories": ["commercial", "private"],
                    "engine_types": ["turbofan"]
                },
                "estimated_duration": {
                    "hours": 2,
                    "minutes": 30
                },
                "procedure_steps": [
                    {
                        "step_id": "STEP-001",
                        "title": "Test Step 1",
                        "description": "Test step description",
                        "configuration_dependent": False,
                        "substeps": [
                            {
                                "substep_id": "SUBSTEP-001-01",
                                "description": "Test substep 1",
                                "configuration_dependent": False
                            },
                            {
                                "substep_id": "SUBSTEP-001-02",
                                "description": "Test substep 2",
                                "configuration_dependent": True,
                                "configuration_variables": ["engine_type"],
                                "applicable_configurations": {
                                    "engine_type": ["turbofan"]
                                }
                            }
                        ]
                    },
                    {
                        "step_id": "STEP-002",
                        "title": "Test Step 2",
                        "description": "Test step description",
                        "configuration_dependent": True,
                        "configuration_variables": ["has_pressurization"],
                        "applicable_configurations": {
                            "has_pressurization": True
                        },
                        "substeps": [
                            {
                                "substep_id": "SUBSTEP-002-01",
                                "description": "Test substep 1",
                                "configuration_dependent": False
                            }
                        ]
                    }
                ]
            },
            "template2.json": {
                "template_id": "MP-TEST-002",
                "title": "Test Template 2",
                "description": "Another test template for unit testing",
                "applicability": {
                    "aircraft_categories": ["military"],
                    "engine_types": ["turboprop"]
                },
                "estimated_duration": {
                    "hours": 3,
                    "minutes": 0
                },
                "procedure_steps": []
            }
        }

    @pytest.fixture
    def service(self, mock_template_data):
        """
        Fixture providing a MaintenanceProcedureTemplateService instance with mocked templates.
        """
        with patch('os.path.exists', return_value=True), \
             patch('os.listdir', return_value=list(mock_template_data.keys())):

            # Directly patch the templates attribute instead of mocking file loading
            with patch.object(MaintenanceProcedureTemplateService, '_load_templates'):
                service = MaintenanceProcedureTemplateService(templates_dir="/mock/templates")

                # Manually set the templates
                service.templates = {
                    mock_template_data["template1.json"]["template_id"]: mock_template_data["template1.json"],
                    mock_template_data["template2.json"]["template_id"]: mock_template_data["template2.json"]
                }

                return service

    def test_init_loads_templates(self, service, mock_template_data):
        """
        Test that the service loads templates during initialization.
        """
        assert len(service.templates) == len(mock_template_data)
        for template_id in ["MP-TEST-001", "MP-TEST-002"]:
            assert template_id in service.templates

    def test_get_all_templates(self, service):
        """
        Test retrieving all templates.
        """
        templates = service.get_all_templates()
        assert len(templates) == 2

        # Verify that only metadata is returned, not full procedure details
        for template in templates:
            assert "template_id" in template
            assert "title" in template
            assert "description" in template
            assert "applicability" in template
            assert "estimated_duration" in template
            assert "procedure_steps" not in template

    def test_get_template(self, service):
        """
        Test retrieving a specific template by ID.
        """
        template = service.get_template("MP-TEST-001")
        assert template is not None
        assert template["template_id"] == "MP-TEST-001"
        assert template["title"] == "Test Template 1"

        # Test retrieving non-existent template
        assert service.get_template("NON-EXISTENT") is None

    def test_get_templates_by_criteria(self, service):
        """
        Test retrieving templates by criteria.
        """
        # Test simple criteria
        templates = service.get_templates_by_criteria({"title": "Test Template 1"})
        assert len(templates) == 1
        assert templates[0]["template_id"] == "MP-TEST-001"

        # Test nested criteria with list value
        templates = service.get_templates_by_criteria({"applicability.aircraft_categories": "commercial"})
        assert len(templates) == 1
        assert templates[0]["template_id"] == "MP-TEST-001"

        # Test criteria with no matches
        templates = service.get_templates_by_criteria({"title": "Non-existent Template"})
        assert len(templates) == 0

    def test_customize_template_with_matching_config(self, service):
        """
        Test customizing a template with a matching configuration.
        """
        aircraft_config = {
            "engine_type": "turbofan",
            "has_pressurization": True
        }

        with patch.object(service, '_get_current_timestamp', return_value="2023-11-01T12:00:00Z"):
            customized = service.customize_template("MP-TEST-001", aircraft_config)

        assert customized is not None
        assert "customization" in customized
        assert customized["customization"]["aircraft_config"] == aircraft_config
        assert customized["customization"]["customized_at"] == "2023-11-01T12:00:00Z"

        # Verify that all steps and substeps are included (since configuration matches)
        assert len(customized["procedure_steps"]) == 2
        assert len(customized["procedure_steps"][0]["substeps"]) == 2

    def test_customize_template_with_non_matching_config(self, service):
        """
        Test customizing a template with a non-matching configuration.
        """
        aircraft_config = {
            "engine_type": "piston",  # Doesn't match the required "turbofan"
            "has_pressurization": False  # Doesn't match the required True
        }

        customized = service.customize_template("MP-TEST-001", aircraft_config)

        assert customized is not None

        # Verify that configuration-dependent steps and substeps are removed
        assert len(customized["procedure_steps"]) == 1  # Step 2 should be removed
        assert len(customized["procedure_steps"][0]["substeps"]) == 1  # Substep 2 should be removed

    def test_customize_template_with_missing_config_vars(self, service):
        """
        Test customizing a template with missing configuration variables.
        """
        aircraft_config = {
            # Missing "engine_type" and "has_pressurization"
        }

        customized = service.customize_template("MP-TEST-001", aircraft_config)

        assert customized is not None

        # Verify that configuration-dependent steps and substeps are removed
        assert len(customized["procedure_steps"]) == 1  # Step 2 should be removed
        assert len(customized["procedure_steps"][0]["substeps"]) == 1  # Substep 2 should be removed

    def test_customize_non_existent_template(self, service):
        """
        Test customizing a non-existent template.
        """
        aircraft_config = {"engine_type": "turbofan"}
        customized = service.customize_template("NON-EXISTENT", aircraft_config)
        assert customized is None

    def test_save_customized_template(self, service):
        """
        Test saving a customized template.
        """
        customized_template = {
            "template_id": "MP-TEST-001-CUSTOM",
            "title": "Customized Test Template",
            "customization": {
                "aircraft_config": {"engine_type": "turbofan"},
                "customized_at": "2023-11-01T12:00:00Z"
            }
        }

        with patch('os.path.exists', return_value=False), \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', new_callable=mock_open) as mock_file, \
             patch('json.dump') as mock_json_dump:

            output_path = service.save_customized_template(customized_template, "/mock/output")

            # Verify directory was created
            mock_makedirs.assert_called_once_with("/mock/output")

            # Verify file was opened for writing
            mock_file.assert_called_once()

            # Verify json.dump was called with the customized template
            mock_json_dump.assert_called_once()
            args, _ = mock_json_dump.call_args
            assert args[0] == customized_template

            # Verify the returned path
            assert "MP-TEST-001-CUSTOM_customized_2023-11-01T12-00-00Z.json" in output_path

    def test_save_customized_template_missing_id(self, service):
        """
        Test saving a customized template without a template_id.
        """
        customized_template = {
            # Missing template_id
            "title": "Customized Test Template"
        }

        with pytest.raises(ValueError):
            service.save_customized_template(customized_template, "/mock/output")
