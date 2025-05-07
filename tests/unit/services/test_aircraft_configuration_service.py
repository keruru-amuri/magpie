"""
Unit tests for the AircraftConfigurationService.
"""
import pytest
from unittest.mock import patch, MagicMock
import os
import json

from app.services.aircraft_configuration_service import AircraftConfigurationService


class TestAircraftConfigurationService:
    """Tests for the AircraftConfigurationService."""

    @pytest.fixture
    def mock_aircraft_types(self):
        """Mock aircraft types data."""
        return [
            {
                "id": "boeing_737",
                "name": "Boeing 737",
                "variants": ["737-700", "737-800", "737-900"],
                "category": "commercial"
            },
            {
                "id": "airbus_a320",
                "name": "Airbus A320",
                "variants": ["A320-200", "A320neo"],
                "category": "commercial"
            },
            {
                "id": "embraer_e190",
                "name": "Embraer E190",
                "variants": ["E190-E2"],
                "category": "regional"
            }
        ]

    @pytest.fixture
    def mock_aircraft_systems(self):
        """Mock aircraft systems data."""
        return [
            {
                "id": "hydraulic",
                "name": "Hydraulic System",
                "description": "Aircraft hydraulic system components and functions",
                "applicable_aircraft_types": ["all"]
            },
            {
                "id": "electrical",
                "name": "Electrical System",
                "description": "Aircraft electrical system components and functions",
                "applicable_aircraft_types": ["all"]
            },
            {
                "id": "avionics",
                "name": "Avionics System",
                "description": "Aircraft avionics system components and functions",
                "applicable_aircraft_types": ["boeing_737", "airbus_a320"]
            }
        ]

    @pytest.fixture
    def mock_procedure_types(self):
        """Mock procedure types data."""
        return [
            {
                "id": "inspection",
                "name": "Inspection",
                "description": "Visual inspection of components",
                "interval": "Daily"
            },
            {
                "id": "functional_test",
                "name": "Functional Test",
                "description": "Testing system functionality",
                "interval": "Weekly"
            },
            {
                "id": "replacement",
                "name": "Replacement",
                "description": "Component replacement procedure",
                "interval": "As needed"
            }
        ]

    @pytest.fixture
    def mock_service(self, mock_aircraft_types, mock_aircraft_systems, mock_procedure_types):
        """Create a mock AircraftConfigurationService."""
        with patch("app.services.aircraft_configuration_service.os.path.exists", return_value=True), \
             patch("app.services.aircraft_configuration_service.get_mock_data_loader") as mock_loader:
            
            # Configure mock loader
            mock_data_loader = MagicMock()
            mock_data_loader.load_file.side_effect = lambda file_path, file_type, source: \
                mock_aircraft_types if "aircraft_types.json" in file_path else \
                mock_aircraft_systems if "aircraft_systems.json" in file_path else \
                mock_procedure_types if "procedure_types.json" in file_path else \
                {}
            
            mock_loader.return_value = mock_data_loader
            
            service = AircraftConfigurationService()
            
            # Manually set the data
            service.aircraft_types = mock_aircraft_types
            service.aircraft_systems = mock_aircraft_systems
            
            return service

    def test_init_and_load_data(self, mock_service):
        """Test initialization and data loading."""
        assert len(mock_service.aircraft_types) == 3
        assert len(mock_service.aircraft_systems) == 3

    def test_get_all_aircraft_types(self, mock_service):
        """Test getting all aircraft types."""
        aircraft_types = mock_service.get_all_aircraft_types()
        assert len(aircraft_types) == 3
        assert any(ac["id"] == "boeing_737" for ac in aircraft_types)
        assert any(ac["id"] == "airbus_a320" for ac in aircraft_types)
        assert any(ac["id"] == "embraer_e190" for ac in aircraft_types)

    def test_get_aircraft_type(self, mock_service):
        """Test getting a specific aircraft type."""
        aircraft_type = mock_service.get_aircraft_type("boeing_737")
        assert aircraft_type is not None
        assert aircraft_type["id"] == "boeing_737"
        assert aircraft_type["name"] == "Boeing 737"

    def test_get_aircraft_type_by_name(self, mock_service):
        """Test getting an aircraft type by name."""
        aircraft_type = mock_service.get_aircraft_type("Boeing 737")
        assert aircraft_type is not None
        assert aircraft_type["id"] == "boeing_737"
        assert aircraft_type["name"] == "Boeing 737"

    def test_get_aircraft_type_not_found(self, mock_service):
        """Test getting a non-existent aircraft type."""
        aircraft_type = mock_service.get_aircraft_type("nonexistent")
        assert aircraft_type is None

    def test_get_all_systems(self, mock_service):
        """Test getting all aircraft systems."""
        systems = mock_service.get_all_systems()
        assert len(systems) == 3
        assert any(sys["id"] == "hydraulic" for sys in systems)
        assert any(sys["id"] == "electrical" for sys in systems)
        assert any(sys["id"] == "avionics" for sys in systems)

    def test_get_system(self, mock_service):
        """Test getting a specific aircraft system."""
        system = mock_service.get_system("hydraulic")
        assert system is not None
        assert system["id"] == "hydraulic"
        assert system["name"] == "Hydraulic System"

    def test_get_system_by_name(self, mock_service):
        """Test getting an aircraft system by name."""
        system = mock_service.get_system("Hydraulic System")
        assert system is not None
        assert system["id"] == "hydraulic"
        assert system["name"] == "Hydraulic System"

    def test_get_system_not_found(self, mock_service):
        """Test getting a non-existent aircraft system."""
        system = mock_service.get_system("nonexistent")
        assert system is None

    def test_get_systems_for_aircraft_type(self, mock_service):
        """Test getting systems for a specific aircraft type."""
        systems = mock_service.get_systems_for_aircraft_type("boeing_737")
        assert len(systems) == 3
        assert any(sys["id"] == "hydraulic" for sys in systems)
        assert any(sys["id"] == "electrical" for sys in systems)
        assert any(sys["id"] == "avionics" for sys in systems)

    def test_get_systems_for_aircraft_type_by_name(self, mock_service):
        """Test getting systems for an aircraft type by name."""
        systems = mock_service.get_systems_for_aircraft_type("Boeing 737")
        assert len(systems) == 3
        assert any(sys["id"] == "hydraulic" for sys in systems)
        assert any(sys["id"] == "electrical" for sys in systems)
        assert any(sys["id"] == "avionics" for sys in systems)

    def test_get_systems_for_nonexistent_aircraft_type(self, mock_service):
        """Test getting systems for a non-existent aircraft type."""
        systems = mock_service.get_systems_for_aircraft_type("nonexistent")
        assert len(systems) == 0

    def test_get_procedure_types_for_system(self, mock_service, mock_procedure_types):
        """Test getting procedure types for a specific aircraft system."""
        with patch("os.path.exists", return_value=True), \
             patch.object(mock_service.mock_data_loader, "load_file", return_value=mock_procedure_types):
            
            procedure_types = mock_service.get_procedure_types_for_system("boeing_737", "hydraulic")
            assert len(procedure_types) == 3
            assert any(pt["id"] == "inspection" for pt in procedure_types)
            assert any(pt["id"] == "functional_test" for pt in procedure_types)
            assert any(pt["id"] == "replacement" for pt in procedure_types)

    def test_get_procedure_types_for_nonexistent_system(self, mock_service):
        """Test getting procedure types for a non-existent aircraft system."""
        procedure_types = mock_service.get_procedure_types_for_system("boeing_737", "nonexistent")
        assert len(procedure_types) == 0

    def test_get_aircraft_configuration(self, mock_service, mock_procedure_types):
        """Test getting aircraft configuration."""
        with patch("os.path.exists", return_value=True), \
             patch.object(mock_service.mock_data_loader, "load_file", return_value=mock_procedure_types):
            
            configuration = mock_service.get_aircraft_configuration("boeing_737")
            assert "aircraft_type" in configuration
            assert "systems" in configuration
            assert "procedure_types" in configuration
            assert configuration["aircraft_type"]["id"] == "boeing_737"
            assert len(configuration["systems"]) == 3
            assert "hydraulic" in configuration["procedure_types"]

    def test_get_aircraft_configuration_nonexistent(self, mock_service):
        """Test getting configuration for a non-existent aircraft type."""
        configuration = mock_service.get_aircraft_configuration("nonexistent")
        assert "error" in configuration
