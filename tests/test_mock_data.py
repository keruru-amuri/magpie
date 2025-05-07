"""Tests for mock data infrastructure."""

import json
import os
import pytest
from pathlib import Path

from app.core.mock.config import MockDataConfig, MockDataSource
from app.core.mock.generator import MockDataGenerator
from app.core.mock.loader import MockDataLoader
from app.core.mock.schema import SchemaValidator
from app.core.mock.service import MockDataService


@pytest.fixture
def temp_mock_data_dir(tmp_path):
    """Create a temporary directory for mock data."""
    # Create mock data directories
    mock_dir = tmp_path / "mock"
    doc_dir = mock_dir / "documentation"
    ts_dir = mock_dir / "troubleshooting"
    maint_dir = mock_dir / "maintenance"
    schemas_dir = mock_dir / "schemas"
    
    for directory in [doc_dir, ts_dir, maint_dir, schemas_dir]:
        directory.mkdir(parents=True, exist_ok=True)
        
    return mock_dir


@pytest.fixture
def mock_config(temp_mock_data_dir):
    """Create a mock data configuration for testing."""
    return MockDataConfig(
        use_mock_data=True,
        paths={
            "base_path": temp_mock_data_dir,
            "documentation_path": temp_mock_data_dir / "documentation",
            "troubleshooting_path": temp_mock_data_dir / "troubleshooting",
            "maintenance_path": temp_mock_data_dir / "maintenance",
            "schemas_path": temp_mock_data_dir / "schemas",
        },
        enable_cache=True,
        validate_schemas=True,
        enable_documentation=True,
        enable_troubleshooting=True,
        enable_maintenance=True,
    )


@pytest.fixture
def mock_generator(mock_config):
    """Create a mock data generator for testing."""
    return MockDataGenerator(config=mock_config)


@pytest.fixture
def mock_loader(mock_config, mock_generator):
    """Create a mock data loader for testing."""
    # Generate mock data
    mock_generator.generate_all_data()
    
    # Create loader
    return MockDataLoader(config=mock_config)


@pytest.fixture
def mock_service(mock_config, mock_loader):
    """Create a mock data service for testing."""
    return MockDataService(config=mock_config, loader=mock_loader)


class TestMockDataConfig:
    """Tests for MockDataConfig."""
    
    def test_is_source_enabled(self, mock_config):
        """Test is_source_enabled method."""
        # All sources should be enabled by default
        assert mock_config.is_source_enabled(MockDataSource.DOCUMENTATION) is True
        assert mock_config.is_source_enabled(MockDataSource.TROUBLESHOOTING) is True
        assert mock_config.is_source_enabled(MockDataSource.MAINTENANCE) is True
        
        # Disable documentation
        mock_config.enable_documentation = False
        assert mock_config.is_source_enabled(MockDataSource.DOCUMENTATION) is False
        assert mock_config.is_source_enabled(MockDataSource.TROUBLESHOOTING) is True
        assert mock_config.is_source_enabled(MockDataSource.MAINTENANCE) is True
        
        # Disable all mock data
        mock_config.use_mock_data = False
        assert mock_config.is_source_enabled(MockDataSource.DOCUMENTATION) is False
        assert mock_config.is_source_enabled(MockDataSource.TROUBLESHOOTING) is False
        assert mock_config.is_source_enabled(MockDataSource.MAINTENANCE) is False


class TestMockDataGenerator:
    """Tests for MockDataGenerator."""
    
    def test_generate_documentation_schemas(self, mock_generator):
        """Test generate_documentation_schemas method."""
        # Generate documentation schemas
        mock_generator.generate_documentation_schemas()
        
        # Check that schemas were created
        schemas_dir = mock_generator.config.paths.schemas_path / MockDataSource.DOCUMENTATION.value
        assert (schemas_dir / "documentation.json").exists()
        assert (schemas_dir / "documentation_list.json").exists()
        
    def test_generate_troubleshooting_schemas(self, mock_generator):
        """Test generate_troubleshooting_schemas method."""
        # Generate troubleshooting schemas
        mock_generator.generate_troubleshooting_schemas()
        
        # Check that schemas were created
        schemas_dir = mock_generator.config.paths.schemas_path / MockDataSource.TROUBLESHOOTING.value
        assert (schemas_dir / "systems.json").exists()
        assert (schemas_dir / "troubleshooting.json").exists()
        assert (schemas_dir / "analysis.json").exists()
        
    def test_generate_maintenance_schemas(self, mock_generator):
        """Test generate_maintenance_schemas method."""
        # Generate maintenance schemas
        mock_generator.generate_maintenance_schemas()
        
        # Check that schemas were created
        schemas_dir = mock_generator.config.paths.schemas_path / MockDataSource.MAINTENANCE.value
        assert (schemas_dir / "aircraft_types.json").exists()
        assert (schemas_dir / "maintenance.json").exists()
        
    def test_generate_all_schemas(self, mock_generator):
        """Test generate_all_schemas method."""
        # Generate all schemas
        mock_generator.generate_all_schemas()
        
        # Check that all schemas were created
        doc_schemas_dir = mock_generator.config.paths.schemas_path / MockDataSource.DOCUMENTATION.value
        ts_schemas_dir = mock_generator.config.paths.schemas_path / MockDataSource.TROUBLESHOOTING.value
        maint_schemas_dir = mock_generator.config.paths.schemas_path / MockDataSource.MAINTENANCE.value
        
        assert (doc_schemas_dir / "documentation.json").exists()
        assert (doc_schemas_dir / "documentation_list.json").exists()
        assert (ts_schemas_dir / "systems.json").exists()
        assert (ts_schemas_dir / "troubleshooting.json").exists()
        assert (ts_schemas_dir / "analysis.json").exists()
        assert (maint_schemas_dir / "aircraft_types.json").exists()
        assert (maint_schemas_dir / "maintenance.json").exists()
        
    def test_generate_documentation_data(self, mock_generator):
        """Test generate_documentation_data method."""
        # Generate documentation schemas first
        mock_generator.generate_documentation_schemas()
        
        # Generate documentation data
        mock_generator.generate_documentation_data()
        
        # Check that data was created
        doc_dir = mock_generator.config.paths.documentation_path
        assert (doc_dir / "index.json").exists()
        assert (doc_dir / "doc-001.json").exists()
        assert (doc_dir / "doc-002.json").exists()
        assert (doc_dir / "doc-003.json").exists()
        
    def test_generate_troubleshooting_data(self, mock_generator):
        """Test generate_troubleshooting_data method."""
        # Generate troubleshooting schemas first
        mock_generator.generate_troubleshooting_schemas()
        
        # Generate troubleshooting data
        mock_generator.generate_troubleshooting_data()
        
        # Check that data was created
        ts_dir = mock_generator.config.paths.troubleshooting_path
        assert (ts_dir / "systems.json").exists()
        assert (ts_dir / "sys-001.json").exists()
        assert (ts_dir / "sys-002.json").exists()
        assert (ts_dir / "sys-001-analysis.json").exists()
        assert (ts_dir / "sys-002-analysis.json").exists()
        
    def test_generate_maintenance_data(self, mock_generator):
        """Test generate_maintenance_data method."""
        # Generate maintenance schemas first
        mock_generator.generate_maintenance_schemas()
        
        # Generate maintenance data
        mock_generator.generate_maintenance_data()
        
        # Check that data was created
        maint_dir = mock_generator.config.paths.maintenance_path
        assert (maint_dir / "aircraft_types.json").exists()
        assert (maint_dir / "ac-001" / "systems.json").exists()
        assert (maint_dir / "ac-001" / "sys-001" / "procedure_types.json").exists()
        assert (maint_dir / "ac-001" / "sys-001" / "proc-001.json").exists()
        
    def test_generate_all_data(self, mock_generator):
        """Test generate_all_data method."""
        # Generate all data
        mock_generator.generate_all_data()
        
        # Check that all data was created
        doc_dir = mock_generator.config.paths.documentation_path
        ts_dir = mock_generator.config.paths.troubleshooting_path
        maint_dir = mock_generator.config.paths.maintenance_path
        
        assert (doc_dir / "index.json").exists()
        assert (doc_dir / "doc-001.json").exists()
        assert (ts_dir / "systems.json").exists()
        assert (ts_dir / "sys-001.json").exists()
        assert (maint_dir / "aircraft_types.json").exists()
        assert (maint_dir / "ac-001" / "systems.json").exists()


class TestMockDataLoader:
    """Tests for MockDataLoader."""
    
    def test_load_documentation(self, mock_loader):
        """Test load_documentation method."""
        # Load documentation
        doc = mock_loader.load_documentation("doc-001")
        
        # Check that documentation was loaded
        assert doc["id"] == "doc-001"
        assert doc["title"] == "Aircraft Maintenance Manual"
        assert doc["type"] == "manual"
        assert len(doc["sections"]) > 0
        
    def test_get_documentation_list(self, mock_loader):
        """Test get_documentation_list method."""
        # Get documentation list
        docs = mock_loader.get_documentation_list()
        
        # Check that documentation list was loaded
        assert len(docs) > 0
        assert docs[0]["id"] == "doc-001"
        assert docs[0]["title"] == "Aircraft Maintenance Manual"
        
    def test_load_troubleshooting(self, mock_loader):
        """Test load_troubleshooting method."""
        # Load troubleshooting data
        ts_data = mock_loader.load_troubleshooting("sys-001")
        
        # Check that troubleshooting data was loaded
        assert ts_data["system_id"] == "sys-001"
        assert ts_data["system_name"] == "Hydraulic System"
        assert len(ts_data["symptoms"]) > 0
        
    def test_get_troubleshooting_systems(self, mock_loader):
        """Test get_troubleshooting_systems method."""
        # Get troubleshooting systems
        systems = mock_loader.get_troubleshooting_systems()
        
        # Check that systems were loaded
        assert len(systems) > 0
        assert systems[0]["id"] == "sys-001"
        assert systems[0]["name"] == "Hydraulic System"
        
    def test_get_maintenance_aircraft_types(self, mock_loader):
        """Test get_maintenance_aircraft_types method."""
        # Get aircraft types
        aircraft_types = mock_loader.get_maintenance_aircraft_types()
        
        # Check that aircraft types were loaded
        assert len(aircraft_types) > 0
        assert aircraft_types[0]["id"] == "ac-001"
        assert aircraft_types[0]["name"] == "Boeing 737"
        
    def test_cache(self, mock_loader):
        """Test caching functionality."""
        # Load documentation
        doc1 = mock_loader.load_documentation("doc-001")
        
        # Load again (should be from cache)
        doc2 = mock_loader.load_documentation("doc-001")
        
        # Should be the same object
        assert doc1 is doc2
        
        # Clear cache
        mock_loader.clear_cache()
        
        # Load again (should be from file)
        doc3 = mock_loader.load_documentation("doc-001")
        
        # Should be a different object
        assert doc1 is not doc3
        
        # But should have the same content
        assert doc1["id"] == doc3["id"]
        assert doc1["title"] == doc3["title"]


class TestMockDataService:
    """Tests for MockDataService."""
    
    def test_get_documentation_list(self, mock_service):
        """Test get_documentation_list method."""
        # Get documentation list
        docs = mock_service.get_documentation_list()
        
        # Check that documentation list was loaded
        assert len(docs) > 0
        assert docs[0]["id"] == "doc-001"
        assert docs[0]["title"] == "Aircraft Maintenance Manual"
        
    def test_get_documentation(self, mock_service):
        """Test get_documentation method."""
        # Get documentation
        doc = mock_service.get_documentation("doc-001")
        
        # Check that documentation was loaded
        assert doc["id"] == "doc-001"
        assert doc["title"] == "Aircraft Maintenance Manual"
        assert doc["type"] == "manual"
        assert len(doc["sections"]) > 0
        
    def test_search_documentation(self, mock_service):
        """Test search_documentation method."""
        # Search documentation
        results = mock_service.search_documentation({"keywords": ["maintenance"]})
        
        # Check that search results were returned
        assert results["query"] == {"keywords": ["maintenance"]}
        assert results["results_count"] > 0
        
    def test_get_troubleshooting_systems(self, mock_service):
        """Test get_troubleshooting_systems method."""
        # Get troubleshooting systems
        systems = mock_service.get_troubleshooting_systems()
        
        # Check that systems were loaded
        assert len(systems) > 0
        assert systems[0]["id"] == "sys-001"
        assert systems[0]["name"] == "Hydraulic System"
        
    def test_get_troubleshooting_symptoms(self, mock_service):
        """Test get_troubleshooting_symptoms method."""
        # Get symptoms for system
        system_data = mock_service.get_troubleshooting_symptoms("sys-001")
        
        # Check that symptoms were loaded
        assert system_data["system_id"] == "sys-001"
        assert system_data["system_name"] == "Hydraulic System"
        assert len(system_data["symptoms"]) > 0
        
    def test_analyze_troubleshooting(self, mock_service):
        """Test analyze_troubleshooting method."""
        # Analyze troubleshooting case
        request = {
            "system": "sys-001",
            "symptoms": ["sym-001", "sym-002"],
            "context": "Routine maintenance inspection",
        }
        analysis = mock_service.analyze_troubleshooting(request)
        
        # Check that analysis was performed
        assert analysis["request"]["system"] == "sys-001"
        assert "analysis" in analysis
        assert "potential_causes" in analysis["analysis"]
        assert "recommended_solutions" in analysis["analysis"]
        
    def test_get_maintenance_aircraft_types(self, mock_service):
        """Test get_maintenance_aircraft_types method."""
        # Get aircraft types
        aircraft_types = mock_service.get_maintenance_aircraft_types()
        
        # Check that aircraft types were loaded
        assert len(aircraft_types) > 0
        assert aircraft_types[0]["id"] == "ac-001"
        assert aircraft_types[0]["name"] == "Boeing 737"
        
    def test_get_maintenance_systems(self, mock_service):
        """Test get_maintenance_systems method."""
        # Get systems for aircraft type
        systems_data = mock_service.get_maintenance_systems("ac-001")
        
        # Check that systems were loaded
        assert systems_data["aircraft_id"] == "ac-001"
        assert "systems" in systems_data
        assert len(systems_data["systems"]) > 0
        
    def test_get_maintenance_procedure_types(self, mock_service):
        """Test get_maintenance_procedure_types method."""
        # Get procedure types for system
        procedure_types_data = mock_service.get_maintenance_procedure_types("ac-001", "sys-001")
        
        # Check that procedure types were loaded
        assert procedure_types_data["system_id"] == "sys-001"
        assert "procedure_types" in procedure_types_data
        assert len(procedure_types_data["procedure_types"]) > 0
        
    def test_generate_maintenance_procedure(self, mock_service):
        """Test generate_maintenance_procedure method."""
        # Generate maintenance procedure
        request = {
            "aircraft_type": "ac-001",
            "system": "sys-001",
            "procedure_type": "proc-001",
            "parameters": {},
        }
        procedure_data = mock_service.generate_maintenance_procedure(request)
        
        # Check that procedure was generated
        assert procedure_data["request"] == request
        assert "procedure" in procedure_data
        assert procedure_data["procedure"]["id"].startswith("maint-")
        assert "steps" in procedure_data["procedure"]
        assert len(procedure_data["procedure"]["steps"]) > 0
