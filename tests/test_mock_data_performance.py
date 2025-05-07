"""Performance tests for mock data infrastructure."""

import json
import time
import statistics
from pathlib import Path

import pytest

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


class TestMockDataPerformance:
    """Performance tests for mock data infrastructure."""
    
    def test_documentation_performance(self, mock_service):
        """Test documentation performance."""
        # Get documentation list
        start_time = time.time()
        docs = mock_service.get_documentation_list()
        end_time = time.time()
        list_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Get documentation for each document
        doc_times = []
        for doc in docs:
            start_time = time.time()
            mock_service.get_documentation(doc["id"])
            end_time = time.time()
            doc_times.append((end_time - start_time) * 1000)  # Convert to milliseconds
            
        # Search documentation
        search_times = []
        for _ in range(10):
            start_time = time.time()
            mock_service.search_documentation({"keywords": ["maintenance"]})
            end_time = time.time()
            search_times.append((end_time - start_time) * 1000)  # Convert to milliseconds
            
        # Calculate statistics
        avg_doc_time = statistics.mean(doc_times)
        p95_doc_time = sorted(doc_times)[int(len(doc_times) * 0.95)]
        p99_doc_time = sorted(doc_times)[int(len(doc_times) * 0.99)]
        
        avg_search_time = statistics.mean(search_times)
        p95_search_time = sorted(search_times)[int(len(search_times) * 0.95)]
        p99_search_time = sorted(search_times)[int(len(search_times) * 0.99)]
        
        # Print results
        print(f"\nDocumentation Performance:")
        print(f"  List Time: {list_time:.2f} ms")
        print(f"  Get Document: Avg={avg_doc_time:.2f} ms, P95={p95_doc_time:.2f} ms, P99={p99_doc_time:.2f} ms")
        print(f"  Search: Avg={avg_search_time:.2f} ms, P95={p95_search_time:.2f} ms, P99={p99_search_time:.2f} ms")
        
        # Assert performance is within acceptable limits
        assert list_time < 100, f"Documentation list time ({list_time:.2f} ms) exceeds limit (100 ms)"
        assert avg_doc_time < 50, f"Average document time ({avg_doc_time:.2f} ms) exceeds limit (50 ms)"
        assert avg_search_time < 100, f"Average search time ({avg_search_time:.2f} ms) exceeds limit (100 ms)"
        
    def test_troubleshooting_performance(self, mock_service):
        """Test troubleshooting performance."""
        # Get systems list
        start_time = time.time()
        systems = mock_service.get_troubleshooting_systems()
        end_time = time.time()
        list_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Get symptoms for each system
        system_times = []
        for system in systems:
            start_time = time.time()
            mock_service.get_troubleshooting_symptoms(system["id"])
            end_time = time.time()
            system_times.append((end_time - start_time) * 1000)  # Convert to milliseconds
            
        # Analyze troubleshooting cases
        analyze_times = []
        for system in systems:
            request = {
                "system": system["id"],
                "symptoms": ["sym-001", "sym-002"],
                "context": "Routine maintenance inspection",
            }
            start_time = time.time()
            mock_service.analyze_troubleshooting(request)
            end_time = time.time()
            analyze_times.append((end_time - start_time) * 1000)  # Convert to milliseconds
            
        # Calculate statistics
        avg_system_time = statistics.mean(system_times)
        p95_system_time = sorted(system_times)[int(len(system_times) * 0.95)]
        p99_system_time = sorted(system_times)[int(len(system_times) * 0.99)]
        
        avg_analyze_time = statistics.mean(analyze_times)
        p95_analyze_time = sorted(analyze_times)[int(len(analyze_times) * 0.95)]
        p99_analyze_time = sorted(analyze_times)[int(len(analyze_times) * 0.99)]
        
        # Print results
        print(f"\nTroubleshooting Performance:")
        print(f"  List Time: {list_time:.2f} ms")
        print(f"  Get Symptoms: Avg={avg_system_time:.2f} ms, P95={p95_system_time:.2f} ms, P99={p99_system_time:.2f} ms")
        print(f"  Analyze: Avg={avg_analyze_time:.2f} ms, P95={p95_analyze_time:.2f} ms, P99={p99_analyze_time:.2f} ms")
        
        # Assert performance is within acceptable limits
        assert list_time < 100, f"Systems list time ({list_time:.2f} ms) exceeds limit (100 ms)"
        assert avg_system_time < 50, f"Average symptoms time ({avg_system_time:.2f} ms) exceeds limit (50 ms)"
        assert avg_analyze_time < 100, f"Average analyze time ({avg_analyze_time:.2f} ms) exceeds limit (100 ms)"
        
    def test_maintenance_performance(self, mock_service):
        """Test maintenance performance."""
        # Get aircraft types list
        start_time = time.time()
        aircraft_types = mock_service.get_maintenance_aircraft_types()
        end_time = time.time()
        list_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Get systems for each aircraft type
        systems_times = []
        for aircraft in aircraft_types:
            start_time = time.time()
            systems_data = mock_service.get_maintenance_systems(aircraft["id"])
            end_time = time.time()
            systems_times.append((end_time - start_time) * 1000)  # Convert to milliseconds
            
        # Generate maintenance procedures
        procedure_times = []
        for aircraft in aircraft_types:
            systems_data = mock_service.get_maintenance_systems(aircraft["id"])
            for system in systems_data["systems"]:
                procedure_types_data = mock_service.get_maintenance_procedure_types(aircraft["id"], system["id"])
                for procedure_type in procedure_types_data["procedure_types"]:
                    request = {
                        "aircraft_type": aircraft["id"],
                        "system": system["id"],
                        "procedure_type": procedure_type["id"],
                        "parameters": {},
                    }
                    start_time = time.time()
                    mock_service.generate_maintenance_procedure(request)
                    end_time = time.time()
                    procedure_times.append((end_time - start_time) * 1000)  # Convert to milliseconds
                    
        # Calculate statistics
        avg_systems_time = statistics.mean(systems_times)
        p95_systems_time = sorted(systems_times)[int(len(systems_times) * 0.95)]
        p99_systems_time = sorted(systems_times)[int(len(systems_times) * 0.99)]
        
        avg_procedure_time = statistics.mean(procedure_times)
        p95_procedure_time = sorted(procedure_times)[int(len(procedure_times) * 0.95)]
        p99_procedure_time = sorted(procedure_times)[int(len(procedure_times) * 0.99)]
        
        # Print results
        print(f"\nMaintenance Performance:")
        print(f"  List Time: {list_time:.2f} ms")
        print(f"  Get Systems: Avg={avg_systems_time:.2f} ms, P95={p95_systems_time:.2f} ms, P99={p99_systems_time:.2f} ms")
        print(f"  Generate Procedure: Avg={avg_procedure_time:.2f} ms, P95={p95_procedure_time:.2f} ms, P99={p99_procedure_time:.2f} ms")
        
        # Assert performance is within acceptable limits
        assert list_time < 100, f"Aircraft types list time ({list_time:.2f} ms) exceeds limit (100 ms)"
        assert avg_systems_time < 50, f"Average systems time ({avg_systems_time:.2f} ms) exceeds limit (50 ms)"
        assert avg_procedure_time < 150, f"Average procedure time ({avg_procedure_time:.2f} ms) exceeds limit (150 ms)"
        
    def test_memory_usage(self, mock_service):
        """Test memory usage."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # Convert to MB
        
        # Perform operations that load data into memory
        mock_service.get_documentation_list()
        for doc_id in ["doc-001", "doc-002", "doc-003", "doc-004", "doc-005"]:
            mock_service.get_documentation(doc_id)
            
        mock_service.get_troubleshooting_systems()
        for system_id in ["sys-001", "sys-002", "sys-003", "sys-004", "sys-005"]:
            mock_service.get_troubleshooting_symptoms(system_id)
            
        mock_service.get_maintenance_aircraft_types()
        for aircraft_id in ["ac-001", "ac-002", "ac-003", "ac-004", "ac-005"]:
            mock_service.get_maintenance_systems(aircraft_id)
            
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # Convert to MB
        memory_increase = final_memory - initial_memory
        
        # Print results
        print(f"\nMemory Usage:")
        print(f"  Initial: {initial_memory:.2f} MB")
        print(f"  Final: {final_memory:.2f} MB")
        print(f"  Increase: {memory_increase:.2f} MB")
        
        # Assert memory usage is within acceptable limits
        assert memory_increase < 100, f"Memory increase ({memory_increase:.2f} MB) exceeds limit (100 MB)"
        
    def test_cache_performance(self, mock_service):
        """Test cache performance."""
        # Clear cache
        mock_service.loader.clear_cache()
        
        # First access (no cache)
        start_time = time.time()
        mock_service.get_documentation("doc-001")
        end_time = time.time()
        no_cache_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Second access (with cache)
        start_time = time.time()
        mock_service.get_documentation("doc-001")
        end_time = time.time()
        with_cache_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Calculate improvement
        improvement = (no_cache_time - with_cache_time) / no_cache_time * 100
        
        # Print results
        print(f"\nCache Performance:")
        print(f"  No Cache: {no_cache_time:.2f} ms")
        print(f"  With Cache: {with_cache_time:.2f} ms")
        print(f"  Improvement: {improvement:.2f}%")
        
        # Assert cache improves performance
        assert with_cache_time < no_cache_time, f"Cache does not improve performance"
        assert improvement > 50, f"Cache improvement ({improvement:.2f}%) is less than expected (50%)"
