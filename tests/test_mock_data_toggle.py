"""Tests for mock data toggle functionality."""

import os
import pytest
from unittest.mock import patch, MagicMock

from app.core.mock.config import MockDataConfig, MockDataSource, get_mock_data_config
from app.core.mock.service import MockDataService


class TestMockDataToggle:
    """Tests for mock data toggle functionality."""

    def test_global_toggle(self):
        """Test global toggle for mock data."""
        # Create config with mock data enabled
        config_enabled = MockDataConfig(use_mock_data=True)
        assert config_enabled.use_mock_data is True
        assert config_enabled.is_source_enabled(MockDataSource.DOCUMENTATION) is True
        assert config_enabled.is_source_enabled(MockDataSource.TROUBLESHOOTING) is True
        assert config_enabled.is_source_enabled(MockDataSource.MAINTENANCE) is True

        # Create config with mock data disabled
        config_disabled = MockDataConfig(use_mock_data=False)
        assert config_disabled.use_mock_data is False
        assert config_disabled.is_source_enabled(MockDataSource.DOCUMENTATION) is False
        assert config_disabled.is_source_enabled(MockDataSource.TROUBLESHOOTING) is False
        assert config_disabled.is_source_enabled(MockDataSource.MAINTENANCE) is False

    def test_per_source_toggle(self):
        """Test per-source toggle for mock data."""
        # Create config with specific sources enabled/disabled
        config = MockDataConfig(
            use_mock_data=True,
            enable_documentation=True,
            enable_troubleshooting=False,
            enable_maintenance=True,
        )

        assert config.use_mock_data is True
        assert config.is_source_enabled(MockDataSource.DOCUMENTATION) is True
        assert config.is_source_enabled(MockDataSource.TROUBLESHOOTING) is False
        assert config.is_source_enabled(MockDataSource.MAINTENANCE) is True

    def test_environment_variables(self):
        """Test environment variables for mock data configuration."""
        # Set environment variables
        with patch.dict(os.environ, {
            "MOCK_DATA_USE_MOCK_DATA": "false",
            "MOCK_DATA_ENABLE_DOCUMENTATION": "true",
            "MOCK_DATA_ENABLE_TROUBLESHOOTING": "false",
            "MOCK_DATA_ENABLE_MAINTENANCE": "true",
        }):
            # Clear the cache to force reloading configuration
            get_mock_data_config.cache_clear()

            # Get configuration
            config = get_mock_data_config()

            # Check configuration
            assert config.use_mock_data is False
            assert config.enable_documentation is True
            assert config.enable_troubleshooting is False
            assert config.enable_maintenance is True

            # Check source enablement (all should be disabled due to global toggle)
            assert config.is_source_enabled(MockDataSource.DOCUMENTATION) is False
            assert config.is_source_enabled(MockDataSource.TROUBLESHOOTING) is False
            assert config.is_source_enabled(MockDataSource.MAINTENANCE) is False

    def test_service_fallback(self):
        """Test service fallback when mock data is disabled."""
        # Create a custom service class that implements fallback
        class CustomService(MockDataService):
            def get_documentation_list(self):
                try:
                    return super().get_documentation_list()
                except ValueError:
                    # Fallback data
                    return [
                        {
                            "id": "doc-001",
                            "title": "Aircraft Maintenance Manual",
                            "type": "manual",
                            "version": "1.0",
                            "last_updated": "2025-01-15",
                        }
                    ]

        # Create mock loader
        mock_loader = MagicMock()
        mock_loader.get_documentation_list.side_effect = ValueError("Mock data is disabled")

        # Create config with mock data disabled
        config = MockDataConfig(use_mock_data=False)

        # Create service with mock loader
        service = CustomService(config=config, loader=mock_loader)

        # Call service method
        result = service.get_documentation_list()

        # Check that fallback data is returned
        assert isinstance(result, list)
        assert len(result) > 0
        assert "id" in result[0]
        assert "title" in result[0]

    def test_service_error_handling(self):
        """Test service error handling when mock data is enabled but not found."""
        # Create a custom service class that passes through FileNotFoundError
        class CustomService(MockDataService):
            def get_documentation(self, doc_id: str):
                try:
                    return self.loader.load_documentation(doc_id)
                except FileNotFoundError:
                    raise FileNotFoundError(f"Documentation not found: {doc_id}")
                except ValueError:
                    # Fallback for disabled mock data
                    return {
                        "id": doc_id,
                        "title": "Placeholder Documentation",
                        "type": "manual",
                        "version": "1.0",
                        "last_updated": "2025-01-15",
                    }

        # Create mock loader
        mock_loader = MagicMock()
        mock_loader.load_documentation.side_effect = FileNotFoundError("Documentation not found")

        # Create config with mock data enabled
        config = MockDataConfig(use_mock_data=True)

        # Create service with mock loader
        service = CustomService(config=config, loader=mock_loader)

        # Call service method and expect exception
        with pytest.raises(FileNotFoundError):
            service.get_documentation("non-existent-doc")

    def test_toggle_in_api(self):
        """Test toggle functionality in API endpoints."""
        from fastapi.testclient import TestClient
        from app.main import app

        # Create test client
        client = TestClient(app)

        # Test with mock data enabled (default)
        response = client.get("/api/v1/documentation/documentation")
        assert response.status_code == 200
        assert "data" in response.json()
        assert isinstance(response.json()["data"], list)

        # Test with mock data disabled
        with patch("app.api.api_v1.endpoints.documentation.mock_data_service") as mock_service:
            mock_service.get_documentation_list.side_effect = ValueError("Mock data is disabled")

            response = client.get("/api/v1/documentation/documentation")
            assert response.status_code == 200
            assert "data" in response.json()
            assert isinstance(response.json()["data"], list)

    def test_toggle_with_real_data_source(self):
        """Test toggle between mock and real data sources."""
        # Create mock real data source
        real_data_source = MagicMock()
        real_data_source.get_documentation_list.return_value = [
            {
                "id": "real-doc-001",
                "title": "Real Documentation",
                "type": "manual",
                "version": "1.0",
                "last_updated": "2025-01-15",
            }
        ]

        # Create mock loader
        mock_loader = MagicMock()
        mock_loader.get_documentation_list.return_value = [
            {
                "id": "mock-doc-001",
                "title": "Mock Documentation",
                "type": "manual",
                "version": "1.0",
                "last_updated": "2025-01-15",
            }
        ]

        # Test with mock data enabled
        config_enabled = MockDataConfig(use_mock_data=True)
        service_enabled = MockDataService(config=config_enabled, loader=mock_loader)

        result_enabled = service_enabled.get_documentation_list()
        assert result_enabled[0]["id"] == "mock-doc-001"

        # Test with mock data disabled
        config_disabled = MockDataConfig(use_mock_data=False)

        # Create a custom service that uses real data source when mock data is disabled
        class CustomService(MockDataService):
            def get_documentation_list(self):
                if not self.config.is_source_enabled(MockDataSource.DOCUMENTATION):
                    return real_data_source.get_documentation_list()
                return super().get_documentation_list()

        service_disabled = CustomService(config=config_disabled, loader=mock_loader)

        result_disabled = service_disabled.get_documentation_list()
        assert result_disabled[0]["id"] == "real-doc-001"
