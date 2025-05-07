"""
Tests for CI/CD integration.

This module contains tests for the CI/CD integration and test data management.
"""
import os
import pytest
import tempfile
from pathlib import Path

from tests.framework.ci_cd.pipeline import (
    TestType, TestStatus, TestResult, TestSuite, TestPipeline
)
from tests.framework.ci_cd.data_management import (
    DataCategory, DataFormat, DataItem, DataSet, DataManager
)
from tests.framework.ci_cd.data_generator import DataGenerator
from tests.framework.ci_cd.config import CIConfig, create_default_config


class TestCICDIntegration:
    """
    Tests for CI/CD integration.
    """
    
    @pytest.fixture
    def temp_dir(self):
        """
        Create temporary directory.
        
        Returns:
            Temporary directory path
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_pipeline_creation(self, temp_dir):
        """
        Test pipeline creation.
        
        Args:
            temp_dir: Temporary directory
        """
        # Create pipeline
        pipeline = TestPipeline(name="Test Pipeline", output_dir=temp_dir)
        
        # Add test suite
        suite = TestSuite(
            name="Unit Tests",
            type=TestType.UNIT,
            command="echo 'Running unit tests'",
            path="tests/unit",
            timeout=10
        )
        
        pipeline.add_suite(suite)
        
        # Verify pipeline
        assert len(pipeline.suites) == 1
        assert pipeline.suites[0].name == "Unit Tests"
        assert pipeline.suites[0].type == TestType.UNIT
    
    def test_pipeline_run(self, temp_dir):
        """
        Test pipeline run.
        
        Args:
            temp_dir: Temporary directory
        """
        # Create pipeline
        pipeline = TestPipeline(name="Test Pipeline", output_dir=temp_dir)
        
        # Add test suite
        suite = TestSuite(
            name="Echo Test",
            type=TestType.UNIT,
            command="echo 'Test passed'",
            path="tests/unit",
            timeout=10
        )
        
        pipeline.add_suite(suite)
        
        # Run pipeline
        results = pipeline.run_all()
        
        # Verify results
        assert "Echo Test" in results
        assert len(results["Echo Test"]) == 1
        assert results["Echo Test"][0].status == TestStatus.PASSED
    
    def test_data_management(self, temp_dir):
        """
        Test data management.
        
        Args:
            temp_dir: Temporary directory
        """
        # Create data manager
        data_dir = Path(temp_dir) / "data"
        manager = DataManager(data_dir=data_dir)
        
        # Create data set
        data_set = manager.create_set(
            name="Test Set",
            description="Test data set",
            tags=["test"]
        )
        
        # Verify data set
        assert data_set.name == "Test Set"
        assert "test" in data_set.tags
        
        # Create test file
        test_file = Path(temp_dir) / "test.txt"
        with open(test_file, "w") as f:
            f.write("Test content")
        
        # Add item
        item = manager.add_item(
            set_id=data_set.id,
            name="Test Item",
            category=DataCategory.DOCUMENTATION,
            format=DataFormat.TEXT,
            source_path=str(test_file),
            tags=["test"]
        )
        
        # Verify item
        assert item is not None
        assert item.name == "Test Item"
        assert item.category == DataCategory.DOCUMENTATION
        assert "test" in item.tags
        
        # Get item
        retrieved_item = manager.get_item(data_set.id, item.id)
        
        # Verify retrieved item
        assert retrieved_item is not None
        assert retrieved_item.id == item.id
        assert retrieved_item.name == "Test Item"
    
    def test_data_generator(self, temp_dir):
        """
        Test data generator.
        
        Args:
            temp_dir: Temporary directory
        """
        # Create data manager
        data_dir = Path(temp_dir) / "data"
        manager = DataManager(data_dir=data_dir)
        
        # Create data generator
        generator = DataGenerator(
            data_manager=manager,
            output_dir=Path(temp_dir) / "generated",
            seed=42
        )
        
        # Generate documentation data
        data_set = generator.generate_documentation_data(
            count=2,
            set_name="Test Documentation"
        )
        
        # Verify data set
        assert data_set.name == "Test Documentation"
        assert len(data_set.items) == 2
        
        # Get items by category
        items = manager.get_items_by_category(DataCategory.DOCUMENTATION)
        
        # Verify items
        assert len(items) == 2
        assert all(item.category == DataCategory.DOCUMENTATION for item in items)
    
    def test_ci_config(self, temp_dir):
        """
        Test CI configuration.
        
        Args:
            temp_dir: Temporary directory
        """
        # Create config file path
        config_file = Path(temp_dir) / "ci_config.json"
        
        # Create CI configuration
        config = CIConfig("Test CI", config_file=config_file)
        
        # Add test suite
        config.add_test_suite(
            name="Unit Tests",
            type=TestType.UNIT,
            command="python -m pytest tests/unit",
            path="tests/unit",
            timeout=300
        )
        
        # Verify test suite
        suites = config.get_test_suites()
        assert "Unit Tests" in suites
        assert suites["Unit Tests"]["type"] == TestType.UNIT.value
        
        # Set threshold
        config.set_threshold("pass_rate", 0.9)
        
        # Verify threshold
        assert config.get_threshold("pass_rate") == 0.9
        
        # Create pipeline
        pipeline = config.create_pipeline(output_dir=temp_dir)
        
        # Verify pipeline
        assert len(pipeline.suites) == 1
        assert pipeline.suites[0].name == "Unit Tests"
        assert pipeline.suites[0].type == TestType.UNIT
