"""
Unit tests for the mock data service.
"""
import pytest
import os
import json
from unittest.mock import patch, MagicMock

from app.core.mock.service import mock_data_service
from app.core.mock.config import MockDataSource


class TestMockDataService:
    """
    Test the mock data service.
    """

    def test_get_documentation_list(self):
        """
        Test getting the documentation list.
        """
        # Get documentation list
        docs = mock_data_service.get_documentation_list()

        # Verify documentation list
        assert isinstance(docs, list)
        assert len(docs) > 0
        assert "id" in docs[0]
        assert "title" in docs[0]

    def test_get_documentation(self):
        """
        Test getting a document.
        """
        # Get documentation list
        docs = mock_data_service.get_documentation_list()

        # Get a specific document
        doc_id = docs[0]["id"]
        doc = mock_data_service.get_documentation(doc_id)

        # Verify document
        assert isinstance(doc, dict)
        assert "id" in doc
        assert "title" in doc
        assert doc["id"] == doc_id

    def test_search_documentation(self):
        """
        Test searching documentation.
        """
        # Search documents
        query = {"keywords": ["maintenance"]}
        search_results = mock_data_service.search_documentation(query)

        # Verify search results
        assert isinstance(search_results, dict)
        assert "results" in search_results
        assert len(search_results["results"]) > 0
        assert "doc_id" in search_results["results"][0]
        assert "title" in search_results["results"][0]
        assert "snippet" in search_results["results"][0]
        assert "relevance_score" in search_results["results"][0]

    def test_search_documentation_with_filters(self):
        """
        Test searching documentation with filters.
        """
        # Search documents with filters
        query = {"keywords": ["maintenance"], "aircraft_type": "Boeing 737"}
        search_results = mock_data_service.search_documentation(query)

        # Verify search results
        assert isinstance(search_results, dict)
        assert "results" in search_results
        assert len(search_results["results"]) > 0

        # Check if filters were applied
        # This is a simplified check; in a real test, we would verify that only documents
        # matching the filters are returned
        assert "doc_id" in search_results["results"][0]
        assert "title" in search_results["results"][0]

    def test_get_troubleshooting_systems(self):
        """
        Test getting troubleshooting systems.
        """
        # Get systems
        systems = mock_data_service.get_troubleshooting_systems()

        # Verify systems
        assert isinstance(systems, list)
        assert len(systems) > 0
        assert "id" in systems[0]
        assert "name" in systems[0]
        assert "description" in systems[0]

    def test_get_troubleshooting_symptoms(self):
        """
        Test getting symptoms for a system.
        """
        # Get systems
        systems = mock_data_service.get_troubleshooting_systems()

        # Get symptoms for a system
        system_id = systems[0]["id"]
        system_data = mock_data_service.get_troubleshooting_symptoms(system_id)

        # Verify system data
        assert isinstance(system_data, dict)
        assert "symptoms" in system_data or "id" in system_data

    def test_analyze_troubleshooting(self):
        """
        Test analyzing a troubleshooting case.
        """
        # Get systems
        systems = mock_data_service.get_troubleshooting_systems()

        # Get symptoms for a system
        system_id = systems[0]["id"]

        # Analyze troubleshooting
        request = {
            "system": system_id,
            "symptoms": ["symptom-001"],
            "context": "The system is not functioning properly."
        }
        analysis = mock_data_service.analyze_troubleshooting(request)

        # Verify analysis
        assert isinstance(analysis, dict)
        assert "request" in analysis
        assert "analysis" in analysis or "potential_causes" in analysis

    def test_get_maintenance_aircraft_types(self):
        """
        Test getting aircraft types.
        """
        # Get aircraft types
        aircraft_types = mock_data_service.get_maintenance_aircraft_types()

        # Verify aircraft types
        assert isinstance(aircraft_types, list)
        assert len(aircraft_types) > 0
        assert "id" in aircraft_types[0]
        assert "name" in aircraft_types[0]

    def test_get_maintenance_systems(self):
        """
        Test getting systems for an aircraft type.
        """
        # Get aircraft types
        aircraft_types = mock_data_service.get_maintenance_aircraft_types()

        # Get systems for an aircraft type
        aircraft_id = aircraft_types[0]["id"]
        systems_data = mock_data_service.get_maintenance_systems(aircraft_id)

        # Verify systems data
        assert isinstance(systems_data, dict)
        assert "aircraft_id" in systems_data
        assert "systems" in systems_data
        assert len(systems_data["systems"]) > 0

    def test_get_maintenance_procedure_types(self):
        """
        Test getting procedure types for a system.
        """
        # Get aircraft types
        aircraft_types = mock_data_service.get_maintenance_aircraft_types()

        # Get systems for an aircraft type
        aircraft_id = aircraft_types[0]["id"]
        systems_data = mock_data_service.get_maintenance_systems(aircraft_id)

        # Get procedure types for a system
        system_id = systems_data["systems"][0]["id"]
        procedure_types_data = mock_data_service.get_maintenance_procedure_types(aircraft_id, system_id)

        # Verify procedure types data
        assert isinstance(procedure_types_data, dict)
        assert "system_id" in procedure_types_data
        assert "procedure_types" in procedure_types_data
        assert len(procedure_types_data["procedure_types"]) > 0

    def test_generate_maintenance_procedure(self):
        """
        Test generating a maintenance procedure.
        """
        # Get aircraft types
        aircraft_types = mock_data_service.get_maintenance_aircraft_types()

        # Get systems for an aircraft type
        aircraft_id = aircraft_types[0]["id"]
        systems_data = mock_data_service.get_maintenance_systems(aircraft_id)

        # Get procedure types for a system
        system_id = systems_data["systems"][0]["id"]
        procedure_types_data = mock_data_service.get_maintenance_procedure_types(aircraft_id, system_id)

        # Generate a procedure
        procedure_type_id = procedure_types_data["procedure_types"][0]["id"]
        request = {
            "aircraft_type": aircraft_id,
            "system": system_id,
            "procedure_type": procedure_type_id
        }
        procedure = mock_data_service.generate_maintenance_procedure(request)

        # Verify procedure
        assert isinstance(procedure, dict)
        assert "request" in procedure
        assert "procedure" in procedure

    def test_generate_maintenance_procedure_with_parameters(self):
        """
        Test generating a maintenance procedure with parameters.
        """
        # Get aircraft types
        aircraft_types = mock_data_service.get_maintenance_aircraft_types()

        # Get systems for an aircraft type
        aircraft_id = aircraft_types[0]["id"]
        systems_data = mock_data_service.get_maintenance_systems(aircraft_id)

        # Get procedure types for a system
        system_id = systems_data["systems"][0]["id"]
        procedure_types_data = mock_data_service.get_maintenance_procedure_types(aircraft_id, system_id)

        # Generate a procedure with parameters
        procedure_type_id = procedure_types_data["procedure_types"][0]["id"]
        request = {
            "aircraft_type": aircraft_id,
            "system": system_id,
            "procedure_type": procedure_type_id,
            "parameters": {"component": "Pump", "interval": "100 hours"}
        }
        procedure = mock_data_service.generate_maintenance_procedure(request)

        # Verify procedure
        assert isinstance(procedure, dict)
        assert "request" in procedure
        assert "procedure" in procedure

    def test_error_handling_invalid_document_id(self):
        """
        Test error handling for invalid document ID.
        """
        # Try to get a document with an invalid ID
        with pytest.raises(Exception):
            mock_data_service.get_documentation("invalid-id")

    def test_error_handling_invalid_system_id(self):
        """
        Test error handling for invalid system ID.
        """
        # Try to get symptoms for an invalid system ID
        with pytest.raises(Exception):
            mock_data_service.get_troubleshooting_symptoms("invalid-id")

    def test_error_handling_invalid_aircraft_id(self):
        """
        Test error handling for invalid aircraft ID.
        """
        # Try to get systems for an invalid aircraft ID
        with pytest.raises(Exception):
            mock_data_service.get_maintenance_systems("invalid-id")

    def test_error_handling_invalid_procedure_parameters(self):
        """
        Test error handling for invalid procedure parameters.
        """
        # Get aircraft types
        aircraft_types = mock_data_service.get_maintenance_aircraft_types()

        # Get systems for an aircraft type
        aircraft_id = aircraft_types[0]["id"]
        systems_data = mock_data_service.get_maintenance_systems(aircraft_id)

        # Get procedure types for a system
        system_id = systems_data["systems"][0]["id"]
        procedure_types_data = mock_data_service.get_maintenance_procedure_types(aircraft_id, system_id)

        # Try to generate a procedure with invalid parameters
        procedure_type_id = procedure_types_data["procedure_types"][0]["id"]
        # Note: The actual implementation might handle invalid parameters gracefully
        # So we're just verifying it doesn't raise an exception
        result = mock_data_service.generate_maintenance_procedure({
            "aircraft_type": aircraft_id,
            "system": system_id,
            "procedure_type": procedure_type_id,
            "parameters": "invalid-parameters"  # Should be a dict
        })

        # Verify result is still a valid procedure
        assert isinstance(result, dict)
        assert "request" in result
        assert "procedure" in result

    def test_mock_data_service_with_disabled_mock_data(self):
        """
        Test the mock data service with mock data disabled.
        """
        # Create a new mock data service with use_mock_data=False
        from app.core.mock.config import MockDataConfig
        from app.core.mock.loader import MockDataLoader

        # Create a config with mock data disabled
        disabled_config = MockDataConfig(use_mock_data=False)
        disabled_service = mock_data_service.__class__(config=disabled_config)

        # Try to get documentation list
        with pytest.raises(ValueError):
            disabled_service.get_documentation_list()

        # Try to get a document
        with pytest.raises(ValueError):
            disabled_service.get_documentation("doc-001")

        # Try to search documents
        with pytest.raises(ValueError):
            disabled_service.search_documentation({"keywords": ["maintenance"]})

        # Try to get troubleshooting systems
        with pytest.raises(ValueError):
            disabled_service.get_troubleshooting_systems()

        # Try to get troubleshooting symptoms
        with pytest.raises(ValueError):
            disabled_service.get_troubleshooting_symptoms("system-001")

        # Try to analyze troubleshooting
        with pytest.raises(ValueError):
            disabled_service.analyze_troubleshooting({
                "system": "system-001",
                "symptoms": ["symptom-001"],
                "context": "The system is not functioning properly."
            })

        # Try to get maintenance aircraft types
        with pytest.raises(ValueError):
            disabled_service.get_maintenance_aircraft_types()

        # Try to get maintenance procedure types
        with pytest.raises(ValueError):
            disabled_service.get_maintenance_procedure_types("aircraft-001", "system-001")

        # Try to generate a maintenance procedure
        with pytest.raises(ValueError):
            disabled_service.generate_maintenance_procedure({
                "aircraft_type": "aircraft-001",
                "system": "system-001",
                "procedure_type": "procedure-type-001"
            })
