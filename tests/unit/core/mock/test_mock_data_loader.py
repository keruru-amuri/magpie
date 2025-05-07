"""
Unit tests for the mock data loader.
"""
import pytest
import os
import json
from unittest.mock import patch, MagicMock

from app.core.mock.loader import (
    load_documentation_data,
    load_troubleshooting_data,
    load_maintenance_data,
    load_all_mock_data,
    get_mock_data_path
)


class TestMockDataLoader:
    """
    Test the mock data loader.
    """
    
    def test_get_mock_data_path(self):
        """
        Test getting the mock data path.
        """
        # Get mock data path
        path = get_mock_data_path()
        
        # Verify path
        assert isinstance(path, str)
        assert os.path.exists(path)
        assert os.path.isdir(path)
    
    def test_load_documentation_data(self):
        """
        Test loading documentation data.
        """
        # Load documentation data
        data = load_documentation_data()
        
        # Verify data
        assert isinstance(data, dict)
        assert "documentation_list" in data
        assert "documentation" in data
        assert isinstance(data["documentation_list"], list)
        assert isinstance(data["documentation"], dict)
        assert len(data["documentation_list"]) > 0
        assert len(data["documentation"]) > 0
    
    def test_load_troubleshooting_data(self):
        """
        Test loading troubleshooting data.
        """
        # Load troubleshooting data
        data = load_troubleshooting_data()
        
        # Verify data
        assert isinstance(data, dict)
        assert "systems" in data
        assert "symptoms" in data
        assert "analysis" in data
        assert isinstance(data["systems"], list)
        assert isinstance(data["symptoms"], dict)
        assert isinstance(data["analysis"], dict)
        assert len(data["systems"]) > 0
        assert len(data["symptoms"]) > 0
        assert len(data["analysis"]) > 0
    
    def test_load_maintenance_data(self):
        """
        Test loading maintenance data.
        """
        # Load maintenance data
        data = load_maintenance_data()
        
        # Verify data
        assert isinstance(data, dict)
        assert "aircraft_types" in data
        assert "systems" in data
        assert "procedure_types" in data
        assert "procedures" in data
        assert isinstance(data["aircraft_types"], list)
        assert isinstance(data["systems"], dict)
        assert isinstance(data["procedure_types"], dict)
        assert isinstance(data["procedures"], dict)
        assert len(data["aircraft_types"]) > 0
        assert len(data["systems"]) > 0
        assert len(data["procedure_types"]) > 0
        assert len(data["procedures"]) > 0
    
    def test_load_all_mock_data(self):
        """
        Test loading all mock data.
        """
        # Load all mock data
        data = load_all_mock_data()
        
        # Verify data
        assert isinstance(data, dict)
        assert "documentation" in data
        assert "troubleshooting" in data
        assert "maintenance" in data
        assert isinstance(data["documentation"], dict)
        assert isinstance(data["troubleshooting"], dict)
        assert isinstance(data["maintenance"], dict)
    
    def test_load_documentation_data_with_invalid_path(self):
        """
        Test loading documentation data with an invalid path.
        """
        # Patch get_mock_data_path to return an invalid path
        with patch("app.core.mock.loader.get_mock_data_path", return_value="/invalid/path"):
            # Try to load documentation data
            with pytest.raises(FileNotFoundError):
                load_documentation_data()
    
    def test_load_troubleshooting_data_with_invalid_path(self):
        """
        Test loading troubleshooting data with an invalid path.
        """
        # Patch get_mock_data_path to return an invalid path
        with patch("app.core.mock.loader.get_mock_data_path", return_value="/invalid/path"):
            # Try to load troubleshooting data
            with pytest.raises(FileNotFoundError):
                load_troubleshooting_data()
    
    def test_load_maintenance_data_with_invalid_path(self):
        """
        Test loading maintenance data with an invalid path.
        """
        # Patch get_mock_data_path to return an invalid path
        with patch("app.core.mock.loader.get_mock_data_path", return_value="/invalid/path"):
            # Try to load maintenance data
            with pytest.raises(FileNotFoundError):
                load_maintenance_data()
    
    def test_load_all_mock_data_with_invalid_path(self):
        """
        Test loading all mock data with an invalid path.
        """
        # Patch get_mock_data_path to return an invalid path
        with patch("app.core.mock.loader.get_mock_data_path", return_value="/invalid/path"):
            # Try to load all mock data
            with pytest.raises(FileNotFoundError):
                load_all_mock_data()
    
    def test_load_documentation_data_with_invalid_json(self):
        """
        Test loading documentation data with invalid JSON.
        """
        # Patch open to return invalid JSON
        mock_open = MagicMock()
        mock_open.return_value.__enter__.return_value.read.return_value = "invalid json"
        
        with patch("builtins.open", mock_open):
            # Try to load documentation data
            with pytest.raises(json.JSONDecodeError):
                load_documentation_data()
    
    def test_load_troubleshooting_data_with_invalid_json(self):
        """
        Test loading troubleshooting data with invalid JSON.
        """
        # Patch open to return invalid JSON
        mock_open = MagicMock()
        mock_open.return_value.__enter__.return_value.read.return_value = "invalid json"
        
        with patch("builtins.open", mock_open):
            # Try to load troubleshooting data
            with pytest.raises(json.JSONDecodeError):
                load_troubleshooting_data()
    
    def test_load_maintenance_data_with_invalid_json(self):
        """
        Test loading maintenance data with invalid JSON.
        """
        # Patch open to return invalid JSON
        mock_open = MagicMock()
        mock_open.return_value.__enter__.return_value.read.return_value = "invalid json"
        
        with patch("builtins.open", mock_open):
            # Try to load maintenance data
            with pytest.raises(json.JSONDecodeError):
                load_maintenance_data()
