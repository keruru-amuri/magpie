"""
Integration tests for the mock data infrastructure.
"""
import pytest
import json
import os
from typing import Dict, List, Any

from app.core.mock.service import mock_data_service
from app.core.agents.documentation_agent import DocumentationAgent
from app.core.agents.troubleshooting_agent import TroubleshootingAgent
from app.core.agents.maintenance_agent import MaintenanceAgent
from app.services.llm_service import LLMService

# Import agent fixtures
pytest_plugins = ["tests.conftest_agent"]


class TestMockDataInfrastructure:
    """
    Integration tests for the mock data infrastructure.
    """
    
    @pytest.fixture
    def llm_service(self):
        """
        Create an LLM service.
        """
        return LLMService()
    
    @pytest.mark.asyncio
    async def test_documentation_mock_data(self, llm_service):
        """
        Test the documentation mock data.
        """
        # Create documentation agent
        agent = DocumentationAgent(
            llm_service=llm_service,
            documentation_service=mock_data_service
        )
        
        # Get documentation list
        docs = await mock_data_service.get_documentation_list()
        
        # Verify documentation list
        assert isinstance(docs, list)
        assert len(docs) > 0
        assert "id" in docs[0]
        assert "title" in docs[0]
        
        # Get a specific document
        doc_id = docs[0]["id"]
        doc = await mock_data_service.get_document(doc_id)
        
        # Verify document
        assert isinstance(doc, dict)
        assert "id" in doc
        assert "title" in doc
        assert "content" in doc
        
        # Search documents
        search_results = await mock_data_service.search_documents("maintenance")
        
        # Verify search results
        assert isinstance(search_results, list)
        assert len(search_results) > 0
        assert "id" in search_results[0]
        assert "title" in search_results[0]
        assert "content" in search_results[0]
        assert "relevance" in search_results[0]
    
    @pytest.mark.asyncio
    async def test_troubleshooting_mock_data(self, llm_service):
        """
        Test the troubleshooting mock data.
        """
        # Create troubleshooting agent
        agent = TroubleshootingAgent(
            llm_service=llm_service,
            troubleshooting_service=mock_data_service
        )
        
        # Get systems
        systems = await mock_data_service.get_systems()
        
        # Verify systems
        assert isinstance(systems, list)
        assert len(systems) > 0
        assert "id" in systems[0]
        assert "name" in systems[0]
        
        # Get symptoms for a system
        system_id = systems[0]["id"]
        symptoms = await mock_data_service.get_symptoms(system_id)
        
        # Verify symptoms
        assert isinstance(symptoms, list)
        assert len(symptoms) > 0
        assert "id" in symptoms[0]
        assert "description" in symptoms[0]
        
        # Diagnose an issue
        diagnosis = await mock_data_service.diagnose_issue(
            system=system_id,
            symptoms=[symptoms[0]["id"]],
            context="The system is not functioning properly."
        )
        
        # Verify diagnosis
        assert isinstance(diagnosis, dict)
        assert "request" in diagnosis
        assert "analysis" in diagnosis
        assert "potential_causes" in diagnosis["analysis"]
        assert "recommended_actions" in diagnosis["analysis"]
    
    @pytest.mark.asyncio
    async def test_maintenance_mock_data(self, llm_service):
        """
        Test the maintenance mock data.
        """
        # Create maintenance agent
        agent = MaintenanceAgent(
            llm_service=llm_service,
            maintenance_service=mock_data_service
        )
        
        # Get aircraft types
        aircraft_types = await mock_data_service.get_aircraft_types()
        
        # Verify aircraft types
        assert isinstance(aircraft_types, list)
        assert len(aircraft_types) > 0
        assert "id" in aircraft_types[0]
        assert "name" in aircraft_types[0]
        
        # Get systems for an aircraft type
        aircraft_id = aircraft_types[0]["id"]
        systems = await mock_data_service.get_systems(aircraft_id)
        
        # Verify systems
        assert isinstance(systems, list)
        assert len(systems) > 0
        assert "id" in systems[0]
        assert "name" in systems[0]
        
        # Get procedure types for a system
        system_id = systems[0]["id"]
        procedure_types = await mock_data_service.get_procedure_types(aircraft_id, system_id)
        
        # Verify procedure types
        assert isinstance(procedure_types, list)
        assert len(procedure_types) > 0
        assert "id" in procedure_types[0]
        assert "name" in procedure_types[0]
        
        # Generate a procedure
        procedure_type_id = procedure_types[0]["id"]
        procedure = await mock_data_service.generate_procedure(
            aircraft_type=aircraft_id,
            system=system_id,
            procedure_type=procedure_type_id
        )
        
        # Verify procedure
        assert isinstance(procedure, dict)
        assert "request" in procedure
        assert "procedure" in procedure
        assert "title" in procedure["procedure"]
        assert "steps" in procedure["procedure"]
    
    def test_mock_data_schema_validation(self):
        """
        Test the mock data schema validation.
        """
        # Get the schema directory
        schema_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "data", "mock", "schemas")
        
        # Verify schema directory exists
        assert os.path.exists(schema_dir), f"Schema directory not found: {schema_dir}"
        
        # Get the data directory
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "data", "mock")
        
        # Verify data directory exists
        assert os.path.exists(data_dir), f"Data directory not found: {data_dir}"
        
        # Load and validate documentation schemas
        self._validate_schema_files(schema_dir, data_dir, "documentation")
        
        # Load and validate troubleshooting schemas
        self._validate_schema_files(schema_dir, data_dir, "troubleshooting")
        
        # Load and validate maintenance schemas
        self._validate_schema_files(schema_dir, data_dir, "maintenance")
    
    def _validate_schema_files(self, schema_dir: str, data_dir: str, category: str):
        """
        Validate schema files for a category.
        
        Args:
            schema_dir: Schema directory
            data_dir: Data directory
            category: Category name
        """
        # Get the schema files
        schema_files = [f for f in os.listdir(os.path.join(schema_dir, category)) if f.endswith(".json")]
        
        # Verify schema files exist
        assert len(schema_files) > 0, f"No schema files found for category: {category}"
        
        # Get the data files
        data_files = []
        category_dir = os.path.join(data_dir, category)
        if os.path.exists(category_dir):
            for root, _, files in os.walk(category_dir):
                for file in files:
                    if file.endswith(".json"):
                        data_files.append(os.path.join(root, file))
        
        # Verify data files exist
        assert len(data_files) > 0, f"No data files found for category: {category}"
        
        # Load schemas
        schemas = {}
        for schema_file in schema_files:
            schema_path = os.path.join(schema_dir, category, schema_file)
            with open(schema_path, "r") as f:
                schema = json.load(f)
                schemas[schema_file] = schema
        
        # Verify schemas loaded
        assert len(schemas) > 0, f"Failed to load schemas for category: {category}"
        
        # Validate data files against schemas
        # Note: This is a simplified validation that just checks if the files can be loaded
        # A full validation would require a JSON Schema validator
        for data_file in data_files:
            with open(data_file, "r") as f:
                try:
                    data = json.load(f)
                    assert isinstance(data, (dict, list)), f"Invalid data format in file: {data_file}"
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON in file: {data_file}")
    
    @pytest.mark.asyncio
    async def test_documentation_agent_with_mock_data(self, llm_service):
        """
        Test the documentation agent with mock data.
        """
        # Create documentation agent
        agent = DocumentationAgent(
            llm_service=llm_service,
            documentation_service=mock_data_service
        )
        
        # Process a query
        result = await agent.process_query(
            query="Where can I find information about landing gear maintenance?",
            conversation_id="test-conversation",
            context={"aircraft_type": "Boeing 737"}
        )
        
        # Verify result
        assert "response" in result
        assert "sources" in result
        assert len(result["sources"]) > 0
    
    @pytest.mark.asyncio
    async def test_troubleshooting_agent_with_mock_data(self, llm_service):
        """
        Test the troubleshooting agent with mock data.
        """
        # Create troubleshooting agent
        agent = TroubleshootingAgent(
            llm_service=llm_service,
            troubleshooting_service=mock_data_service
        )
        
        # Process a query
        result = await agent.process_query(
            query="The hydraulic system is making unusual noises and showing low pressure.",
            conversation_id="test-conversation",
            context={"aircraft_type": "Boeing 737"}
        )
        
        # Verify result
        assert "response" in result
        assert "diagnosis" in result
        assert result["diagnosis"] is not None
    
    @pytest.mark.asyncio
    async def test_maintenance_agent_with_mock_data(self, llm_service):
        """
        Test the maintenance agent with mock data.
        """
        # Create maintenance agent
        agent = MaintenanceAgent(
            llm_service=llm_service,
            maintenance_service=mock_data_service
        )
        
        # Process a query
        result = await agent.process_query(
            query="What are the steps to inspect the hydraulic pump on a Boeing 737?",
            conversation_id="test-conversation",
            context={"aircraft_type": "Boeing 737"}
        )
        
        # Verify result
        assert "response" in result
        assert "procedure" in result
        assert result["procedure"] is not None
