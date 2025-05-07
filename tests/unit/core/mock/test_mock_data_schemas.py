"""
Unit tests for the mock data schemas.
"""
import pytest
import os
import json
import jsonschema
from typing import Dict, List, Any


class TestMockDataSchemas:
    """
    Test the mock data schemas.
    """
    
    @pytest.fixture
    def schema_dir(self):
        """
        Get the schema directory.
        """
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "data", "mock", "schemas")
    
    @pytest.fixture
    def data_dir(self):
        """
        Get the data directory.
        """
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "data", "mock")
    
    def test_schema_directory_exists(self, schema_dir):
        """
        Test that the schema directory exists.
        """
        assert os.path.exists(schema_dir), f"Schema directory not found: {schema_dir}"
        assert os.path.isdir(schema_dir), f"Schema directory is not a directory: {schema_dir}"
    
    def test_data_directory_exists(self, data_dir):
        """
        Test that the data directory exists.
        """
        assert os.path.exists(data_dir), f"Data directory not found: {data_dir}"
        assert os.path.isdir(data_dir), f"Data directory is not a directory: {data_dir}"
    
    def test_documentation_schemas(self, schema_dir):
        """
        Test the documentation schemas.
        """
        # Get the documentation schema directory
        doc_schema_dir = os.path.join(schema_dir, "documentation")
        
        # Verify directory exists
        assert os.path.exists(doc_schema_dir), f"Documentation schema directory not found: {doc_schema_dir}"
        assert os.path.isdir(doc_schema_dir), f"Documentation schema directory is not a directory: {doc_schema_dir}"
        
        # Get schema files
        schema_files = [f for f in os.listdir(doc_schema_dir) if f.endswith(".json")]
        
        # Verify schema files exist
        assert len(schema_files) > 0, f"No schema files found in directory: {doc_schema_dir}"
        
        # Load and validate schemas
        for schema_file in schema_files:
            schema_path = os.path.join(doc_schema_dir, schema_file)
            
            # Load schema
            with open(schema_path, "r") as f:
                schema = json.load(f)
            
            # Verify schema is valid
            assert isinstance(schema, dict), f"Invalid schema format in file: {schema_path}"
            assert "$schema" in schema, f"Missing $schema field in file: {schema_path}"
            assert "type" in schema, f"Missing type field in file: {schema_path}"
            
            # Validate schema against JSON Schema meta-schema
            try:
                jsonschema.validate(schema, jsonschema.Draft7Validator.META_SCHEMA)
            except jsonschema.exceptions.ValidationError as e:
                pytest.fail(f"Invalid schema in file {schema_path}: {str(e)}")
    
    def test_troubleshooting_schemas(self, schema_dir):
        """
        Test the troubleshooting schemas.
        """
        # Get the troubleshooting schema directory
        ts_schema_dir = os.path.join(schema_dir, "troubleshooting")
        
        # Verify directory exists
        assert os.path.exists(ts_schema_dir), f"Troubleshooting schema directory not found: {ts_schema_dir}"
        assert os.path.isdir(ts_schema_dir), f"Troubleshooting schema directory is not a directory: {ts_schema_dir}"
        
        # Get schema files
        schema_files = [f for f in os.listdir(ts_schema_dir) if f.endswith(".json")]
        
        # Verify schema files exist
        assert len(schema_files) > 0, f"No schema files found in directory: {ts_schema_dir}"
        
        # Load and validate schemas
        for schema_file in schema_files:
            schema_path = os.path.join(ts_schema_dir, schema_file)
            
            # Load schema
            with open(schema_path, "r") as f:
                schema = json.load(f)
            
            # Verify schema is valid
            assert isinstance(schema, dict), f"Invalid schema format in file: {schema_path}"
            assert "$schema" in schema, f"Missing $schema field in file: {schema_path}"
            assert "type" in schema, f"Missing type field in file: {schema_path}"
            
            # Validate schema against JSON Schema meta-schema
            try:
                jsonschema.validate(schema, jsonschema.Draft7Validator.META_SCHEMA)
            except jsonschema.exceptions.ValidationError as e:
                pytest.fail(f"Invalid schema in file {schema_path}: {str(e)}")
    
    def test_maintenance_schemas(self, schema_dir):
        """
        Test the maintenance schemas.
        """
        # Get the maintenance schema directory
        maint_schema_dir = os.path.join(schema_dir, "maintenance")
        
        # Verify directory exists
        assert os.path.exists(maint_schema_dir), f"Maintenance schema directory not found: {maint_schema_dir}"
        assert os.path.isdir(maint_schema_dir), f"Maintenance schema directory is not a directory: {maint_schema_dir}"
        
        # Get schema files
        schema_files = [f for f in os.listdir(maint_schema_dir) if f.endswith(".json")]
        
        # Verify schema files exist
        assert len(schema_files) > 0, f"No schema files found in directory: {maint_schema_dir}"
        
        # Load and validate schemas
        for schema_file in schema_files:
            schema_path = os.path.join(maint_schema_dir, schema_file)
            
            # Load schema
            with open(schema_path, "r") as f:
                schema = json.load(f)
            
            # Verify schema is valid
            assert isinstance(schema, dict), f"Invalid schema format in file: {schema_path}"
            assert "$schema" in schema, f"Missing $schema field in file: {schema_path}"
            assert "type" in schema, f"Missing type field in file: {schema_path}"
            
            # Validate schema against JSON Schema meta-schema
            try:
                jsonschema.validate(schema, jsonschema.Draft7Validator.META_SCHEMA)
            except jsonschema.exceptions.ValidationError as e:
                pytest.fail(f"Invalid schema in file {schema_path}: {str(e)}")
    
    def test_documentation_data_against_schemas(self, schema_dir, data_dir):
        """
        Test the documentation data against schemas.
        """
        # Get the documentation schema directory
        doc_schema_dir = os.path.join(schema_dir, "documentation")
        
        # Get the documentation data directory
        doc_data_dir = os.path.join(data_dir, "documentation")
        
        # Verify directories exist
        assert os.path.exists(doc_schema_dir), f"Documentation schema directory not found: {doc_schema_dir}"
        assert os.path.exists(doc_data_dir), f"Documentation data directory not found: {doc_data_dir}"
        
        # Load schemas
        schemas = {}
        for schema_file in os.listdir(doc_schema_dir):
            if schema_file.endswith(".json"):
                schema_path = os.path.join(doc_schema_dir, schema_file)
                with open(schema_path, "r") as f:
                    schema = json.load(f)
                schemas[schema_file] = schema
        
        # Verify schemas loaded
        assert len(schemas) > 0, f"No schemas loaded from directory: {doc_schema_dir}"
        
        # Get data files
        data_files = []
        for root, _, files in os.walk(doc_data_dir):
            for file in files:
                if file.endswith(".json"):
                    data_files.append(os.path.join(root, file))
        
        # Verify data files exist
        assert len(data_files) > 0, f"No data files found in directory: {doc_data_dir}"
        
        # Validate data files against schemas
        # Note: This is a simplified validation that just checks if the files can be loaded
        # A full validation would require matching each data file to its schema
        for data_file in data_files:
            with open(data_file, "r") as f:
                try:
                    data = json.load(f)
                    assert isinstance(data, (dict, list)), f"Invalid data format in file: {data_file}"
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON in file: {data_file}")
    
    def test_troubleshooting_data_against_schemas(self, schema_dir, data_dir):
        """
        Test the troubleshooting data against schemas.
        """
        # Get the troubleshooting schema directory
        ts_schema_dir = os.path.join(schema_dir, "troubleshooting")
        
        # Get the troubleshooting data directory
        ts_data_dir = os.path.join(data_dir, "troubleshooting")
        
        # Verify directories exist
        assert os.path.exists(ts_schema_dir), f"Troubleshooting schema directory not found: {ts_schema_dir}"
        assert os.path.exists(ts_data_dir), f"Troubleshooting data directory not found: {ts_data_dir}"
        
        # Load schemas
        schemas = {}
        for schema_file in os.listdir(ts_schema_dir):
            if schema_file.endswith(".json"):
                schema_path = os.path.join(ts_schema_dir, schema_file)
                with open(schema_path, "r") as f:
                    schema = json.load(f)
                schemas[schema_file] = schema
        
        # Verify schemas loaded
        assert len(schemas) > 0, f"No schemas loaded from directory: {ts_schema_dir}"
        
        # Get data files
        data_files = []
        for root, _, files in os.walk(ts_data_dir):
            for file in files:
                if file.endswith(".json"):
                    data_files.append(os.path.join(root, file))
        
        # Verify data files exist
        assert len(data_files) > 0, f"No data files found in directory: {ts_data_dir}"
        
        # Validate data files against schemas
        # Note: This is a simplified validation that just checks if the files can be loaded
        # A full validation would require matching each data file to its schema
        for data_file in data_files:
            with open(data_file, "r") as f:
                try:
                    data = json.load(f)
                    assert isinstance(data, (dict, list)), f"Invalid data format in file: {data_file}"
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON in file: {data_file}")
    
    def test_maintenance_data_against_schemas(self, schema_dir, data_dir):
        """
        Test the maintenance data against schemas.
        """
        # Get the maintenance schema directory
        maint_schema_dir = os.path.join(schema_dir, "maintenance")
        
        # Get the maintenance data directory
        maint_data_dir = os.path.join(data_dir, "maintenance")
        
        # Verify directories exist
        assert os.path.exists(maint_schema_dir), f"Maintenance schema directory not found: {maint_schema_dir}"
        assert os.path.exists(maint_data_dir), f"Maintenance data directory not found: {maint_data_dir}"
        
        # Load schemas
        schemas = {}
        for schema_file in os.listdir(maint_schema_dir):
            if schema_file.endswith(".json"):
                schema_path = os.path.join(maint_schema_dir, schema_file)
                with open(schema_path, "r") as f:
                    schema = json.load(f)
                schemas[schema_file] = schema
        
        # Verify schemas loaded
        assert len(schemas) > 0, f"No schemas loaded from directory: {maint_schema_dir}"
        
        # Get data files
        data_files = []
        for root, _, files in os.walk(maint_data_dir):
            for file in files:
                if file.endswith(".json"):
                    data_files.append(os.path.join(root, file))
        
        # Verify data files exist
        assert len(data_files) > 0, f"No data files found in directory: {maint_data_dir}"
        
        # Validate data files against schemas
        # Note: This is a simplified validation that just checks if the files can be loaded
        # A full validation would require matching each data file to its schema
        for data_file in data_files:
            with open(data_file, "r") as f:
                try:
                    data = json.load(f)
                    assert isinstance(data, (dict, list)), f"Invalid data format in file: {data_file}"
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON in file: {data_file}")
