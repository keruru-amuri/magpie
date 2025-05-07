"""
Unit tests for the mock data configuration.
"""
import pytest
import os
from unittest.mock import patch, MagicMock

from app.core.mock.config import (
    is_mock_data_enabled,
    get_mock_data_path,
    set_mock_data_enabled,
    set_mock_data_path
)


class TestMockDataConfig:
    """
    Test the mock data configuration.
    """
    
    def test_is_mock_data_enabled(self):
        """
        Test checking if mock data is enabled.
        """
        # Test with environment variable set to "true"
        with patch.dict(os.environ, {"MAGPIE_MOCK_DATA_ENABLED": "true"}):
            assert is_mock_data_enabled() is True
        
        # Test with environment variable set to "false"
        with patch.dict(os.environ, {"MAGPIE_MOCK_DATA_ENABLED": "false"}):
            assert is_mock_data_enabled() is False
        
        # Test with environment variable set to "1"
        with patch.dict(os.environ, {"MAGPIE_MOCK_DATA_ENABLED": "1"}):
            assert is_mock_data_enabled() is True
        
        # Test with environment variable set to "0"
        with patch.dict(os.environ, {"MAGPIE_MOCK_DATA_ENABLED": "0"}):
            assert is_mock_data_enabled() is False
        
        # Test with environment variable not set
        with patch.dict(os.environ, {}, clear=True):
            # Default should be True for development
            assert is_mock_data_enabled() is True
    
    def test_get_mock_data_path(self):
        """
        Test getting the mock data path.
        """
        # Test with environment variable set
        test_path = "/test/path"
        with patch.dict(os.environ, {"MAGPIE_MOCK_DATA_PATH": test_path}):
            assert get_mock_data_path() == test_path
        
        # Test with environment variable not set
        with patch.dict(os.environ, {}, clear=True):
            # Should return a default path
            path = get_mock_data_path()
            assert isinstance(path, str)
            assert len(path) > 0
            assert "data" in path.lower()
            assert "mock" in path.lower()
    
    def test_set_mock_data_enabled(self):
        """
        Test setting mock data enabled.
        """
        # Test setting to True
        with patch.dict(os.environ, {}, clear=True):
            set_mock_data_enabled(True)
            assert os.environ.get("MAGPIE_MOCK_DATA_ENABLED") == "true"
        
        # Test setting to False
        with patch.dict(os.environ, {}, clear=True):
            set_mock_data_enabled(False)
            assert os.environ.get("MAGPIE_MOCK_DATA_ENABLED") == "false"
    
    def test_set_mock_data_path(self):
        """
        Test setting the mock data path.
        """
        # Test setting a path
        test_path = "/test/path"
        with patch.dict(os.environ, {}, clear=True):
            set_mock_data_path(test_path)
            assert os.environ.get("MAGPIE_MOCK_DATA_PATH") == test_path
        
        # Test setting None
        with patch.dict(os.environ, {"MAGPIE_MOCK_DATA_PATH": test_path}):
            set_mock_data_path(None)
            assert "MAGPIE_MOCK_DATA_PATH" not in os.environ
    
    def test_is_mock_data_enabled_with_invalid_value(self):
        """
        Test checking if mock data is enabled with an invalid value.
        """
        # Test with environment variable set to an invalid value
        with patch.dict(os.environ, {"MAGPIE_MOCK_DATA_ENABLED": "invalid"}):
            # Should default to True for development
            assert is_mock_data_enabled() is True
    
    def test_get_mock_data_path_with_nonexistent_path(self):
        """
        Test getting the mock data path with a nonexistent path.
        """
        # Test with environment variable set to a nonexistent path
        test_path = "/nonexistent/path"
        with patch.dict(os.environ, {"MAGPIE_MOCK_DATA_PATH": test_path}):
            # Should return the path even if it doesn't exist
            assert get_mock_data_path() == test_path
    
    def test_set_mock_data_enabled_with_invalid_value(self):
        """
        Test setting mock data enabled with an invalid value.
        """
        # Test setting to None
        with patch.dict(os.environ, {}, clear=True):
            set_mock_data_enabled(None)
            assert os.environ.get("MAGPIE_MOCK_DATA_ENABLED") == "false"
        
        # Test setting to a string
        with patch.dict(os.environ, {}, clear=True):
            set_mock_data_enabled("invalid")
            assert os.environ.get("MAGPIE_MOCK_DATA_ENABLED") == "true"
        
        # Test setting to a number
        with patch.dict(os.environ, {}, clear=True):
            set_mock_data_enabled(1)
            assert os.environ.get("MAGPIE_MOCK_DATA_ENABLED") == "true"
    
    def test_set_mock_data_path_with_invalid_value(self):
        """
        Test setting the mock data path with an invalid value.
        """
        # Test setting to a non-string value
        with patch.dict(os.environ, {}, clear=True):
            set_mock_data_path(123)
            assert os.environ.get("MAGPIE_MOCK_DATA_PATH") == "123"
        
        # Test setting to an empty string
        with patch.dict(os.environ, {}, clear=True):
            set_mock_data_path("")
            assert "MAGPIE_MOCK_DATA_PATH" not in os.environ
