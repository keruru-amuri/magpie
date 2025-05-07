"""
Unit tests for the mock data generator.
"""
import pytest
import os
import json
from unittest.mock import patch, MagicMock

from app.core.mock.generator import (
    generate_documentation_data,
    generate_troubleshooting_data,
    generate_maintenance_data,
    generate_all_data,
    validate_schema
)


class TestMockDataGenerator:
    """
    Test the mock data generator.
    """
    
    def test_validate_schema(self):
        """
        Test schema validation.
        """
        # Create a simple schema
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "age": {"type": "number"}
            },
            "required": ["id", "name"]
        }
        
        # Create valid data
        valid_data = {
            "id": "123",
            "name": "John Doe",
            "age": 30
        }
        
        # Create invalid data (missing required field)
        invalid_data_1 = {
            "id": "123",
            "age": 30
        }
        
        # Create invalid data (wrong type)
        invalid_data_2 = {
            "id": "123",
            "name": "John Doe",
            "age": "thirty"
        }
        
        # Validate valid data
        result = validate_schema(valid_data, schema)
        assert result is True
        
        # Validate invalid data (missing required field)
        result = validate_schema(invalid_data_1, schema)
        assert result is False
        
        # Validate invalid data (wrong type)
        result = validate_schema(invalid_data_2, schema)
        assert result is False
    
    @patch("app.core.mock.generator.validate_schema", return_value=True)
    @patch("app.core.mock.generator.save_json_file")
    def test_generate_documentation_data(self, mock_save_json, mock_validate):
        """
        Test generating documentation data.
        """
        # Generate documentation data
        result = generate_documentation_data(num_documents=5, output_dir="/tmp")
        
        # Verify result
        assert result is True
        
        # Verify validate_schema was called
        assert mock_validate.call_count > 0
        
        # Verify save_json_file was called
        assert mock_save_json.call_count > 0
    
    @patch("app.core.mock.generator.validate_schema", return_value=True)
    @patch("app.core.mock.generator.save_json_file")
    def test_generate_troubleshooting_data(self, mock_save_json, mock_validate):
        """
        Test generating troubleshooting data.
        """
        # Generate troubleshooting data
        result = generate_troubleshooting_data(num_systems=3, num_symptoms=5, output_dir="/tmp")
        
        # Verify result
        assert result is True
        
        # Verify validate_schema was called
        assert mock_validate.call_count > 0
        
        # Verify save_json_file was called
        assert mock_save_json.call_count > 0
    
    @patch("app.core.mock.generator.validate_schema", return_value=True)
    @patch("app.core.mock.generator.save_json_file")
    def test_generate_maintenance_data(self, mock_save_json, mock_validate):
        """
        Test generating maintenance data.
        """
        # Generate maintenance data
        result = generate_maintenance_data(num_aircraft=2, num_systems=3, num_procedures=4, output_dir="/tmp")
        
        # Verify result
        assert result is True
        
        # Verify validate_schema was called
        assert mock_validate.call_count > 0
        
        # Verify save_json_file was called
        assert mock_save_json.call_count > 0
    
    @patch("app.core.mock.generator.generate_documentation_data", return_value=True)
    @patch("app.core.mock.generator.generate_troubleshooting_data", return_value=True)
    @patch("app.core.mock.generator.generate_maintenance_data", return_value=True)
    def test_generate_all_data(self, mock_maintenance, mock_troubleshooting, mock_documentation):
        """
        Test generating all data.
        """
        # Generate all data
        result = generate_all_data(output_dir="/tmp")
        
        # Verify result
        assert result is True
        
        # Verify generate_documentation_data was called
        mock_documentation.assert_called_once()
        
        # Verify generate_troubleshooting_data was called
        mock_troubleshooting.assert_called_once()
        
        # Verify generate_maintenance_data was called
        mock_maintenance.assert_called_once()
    
    @patch("app.core.mock.generator.validate_schema", return_value=False)
    @patch("app.core.mock.generator.save_json_file")
    def test_generate_documentation_data_with_invalid_schema(self, mock_save_json, mock_validate):
        """
        Test generating documentation data with invalid schema.
        """
        # Generate documentation data
        result = generate_documentation_data(num_documents=5, output_dir="/tmp")
        
        # Verify result
        assert result is False
        
        # Verify validate_schema was called
        assert mock_validate.call_count > 0
        
        # Verify save_json_file was not called
        mock_save_json.assert_not_called()
    
    @patch("app.core.mock.generator.validate_schema", return_value=False)
    @patch("app.core.mock.generator.save_json_file")
    def test_generate_troubleshooting_data_with_invalid_schema(self, mock_save_json, mock_validate):
        """
        Test generating troubleshooting data with invalid schema.
        """
        # Generate troubleshooting data
        result = generate_troubleshooting_data(num_systems=3, num_symptoms=5, output_dir="/tmp")
        
        # Verify result
        assert result is False
        
        # Verify validate_schema was called
        assert mock_validate.call_count > 0
        
        # Verify save_json_file was not called
        mock_save_json.assert_not_called()
    
    @patch("app.core.mock.generator.validate_schema", return_value=False)
    @patch("app.core.mock.generator.save_json_file")
    def test_generate_maintenance_data_with_invalid_schema(self, mock_save_json, mock_validate):
        """
        Test generating maintenance data with invalid schema.
        """
        # Generate maintenance data
        result = generate_maintenance_data(num_aircraft=2, num_systems=3, num_procedures=4, output_dir="/tmp")
        
        # Verify result
        assert result is False
        
        # Verify validate_schema was called
        assert mock_validate.call_count > 0
        
        # Verify save_json_file was not called
        mock_save_json.assert_not_called()
    
    @patch("app.core.mock.generator.generate_documentation_data", return_value=False)
    @patch("app.core.mock.generator.generate_troubleshooting_data", return_value=True)
    @patch("app.core.mock.generator.generate_maintenance_data", return_value=True)
    def test_generate_all_data_with_documentation_failure(self, mock_maintenance, mock_troubleshooting, mock_documentation):
        """
        Test generating all data with documentation failure.
        """
        # Generate all data
        result = generate_all_data(output_dir="/tmp")
        
        # Verify result
        assert result is False
        
        # Verify generate_documentation_data was called
        mock_documentation.assert_called_once()
        
        # Verify generate_troubleshooting_data was not called
        mock_troubleshooting.assert_not_called()
        
        # Verify generate_maintenance_data was not called
        mock_maintenance.assert_not_called()
    
    @patch("app.core.mock.generator.generate_documentation_data", return_value=True)
    @patch("app.core.mock.generator.generate_troubleshooting_data", return_value=False)
    @patch("app.core.mock.generator.generate_maintenance_data", return_value=True)
    def test_generate_all_data_with_troubleshooting_failure(self, mock_maintenance, mock_troubleshooting, mock_documentation):
        """
        Test generating all data with troubleshooting failure.
        """
        # Generate all data
        result = generate_all_data(output_dir="/tmp")
        
        # Verify result
        assert result is False
        
        # Verify generate_documentation_data was called
        mock_documentation.assert_called_once()
        
        # Verify generate_troubleshooting_data was called
        mock_troubleshooting.assert_called_once()
        
        # Verify generate_maintenance_data was not called
        mock_maintenance.assert_not_called()
    
    @patch("app.core.mock.generator.generate_documentation_data", return_value=True)
    @patch("app.core.mock.generator.generate_troubleshooting_data", return_value=True)
    @patch("app.core.mock.generator.generate_maintenance_data", return_value=False)
    def test_generate_all_data_with_maintenance_failure(self, mock_maintenance, mock_troubleshooting, mock_documentation):
        """
        Test generating all data with maintenance failure.
        """
        # Generate all data
        result = generate_all_data(output_dir="/tmp")
        
        # Verify result
        assert result is False
        
        # Verify generate_documentation_data was called
        mock_documentation.assert_called_once()
        
        # Verify generate_troubleshooting_data was called
        mock_troubleshooting.assert_called_once()
        
        # Verify generate_maintenance_data was called
        mock_maintenance.assert_called_once()
