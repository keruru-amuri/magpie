# MAGPIE Mock Data Infrastructure

This document provides comprehensive documentation for the mock data infrastructure implemented for the MAGPIE platform.

## Overview

The mock data infrastructure provides realistic test data for the three primary agent use cases:

1. **Technical Documentation Assistant**
2. **Troubleshooting Advisor**
3. **Maintenance Procedure Generator**

The infrastructure is designed to be flexible, configurable, and to closely mimic production data patterns.

## Directory Structure

```
data/
└── mock/
    ├── documentation/     # Mock data for Technical Documentation Assistant
    ├── troubleshooting/   # Mock data for Troubleshooting Advisor
    ├── maintenance/       # Mock data for Maintenance Procedure Generator
    └── schemas/           # JSON schemas for all data types
        ├── documentation/
        ├── troubleshooting/
        └── maintenance/
```

## Core Components

The mock data infrastructure consists of several core components:

### 1. Configuration (`app/core/mock/config.py`)

The configuration module provides settings for the mock data infrastructure:

- Enable/disable mock data globally or per use case
- Configure paths to mock data files
- Control caching behavior
- Toggle schema validation
- Simulate network latency for realistic testing

**Usage Example:**

```python
from app.core.mock.config import mock_data_config

# Check if mock data is enabled
if mock_data_config.use_mock_data:
    # Use mock data
    pass
else:
    # Use real data
    pass

# Enable/disable specific use cases
mock_data_config.enable_documentation = True
mock_data_config.enable_troubleshooting = False
mock_data_config.enable_maintenance = True

# Configure cache
mock_data_config.enable_cache = True
mock_data_config.cache_ttl_seconds = 300  # 5 minutes
```

### 2. Schema Validation (`app/core/mock/schema.py`)

The schema validation module ensures that mock data conforms to defined JSON schemas:

- Validate data against JSON schemas
- Report validation errors
- Cache schemas for performance

**Usage Example:**

```python
from app.core.mock.schema import SchemaValidator
from app.core.mock.config import MockDataSource

validator = SchemaValidator()

# Validate data against a schema
data = {"id": "doc-001", "title": "Aircraft Maintenance Manual", ...}
errors = validator.validate(data, "documentation.json", MockDataSource.DOCUMENTATION)

if errors:
    print(f"Validation errors: {errors}")
else:
    print("Data is valid")

# Check if data is valid
is_valid = validator.is_valid(data, "documentation.json", MockDataSource.DOCUMENTATION)
```

### 3. Data Loading (`app/core/mock/loader.py`)

The data loader module provides utilities for loading mock data:

- Load data from JSON, YAML, or text files
- Cache frequently accessed data
- Simulate network latency
- Handle file not found and other errors

**Usage Example:**

```python
from app.core.mock.loader import mock_data_loader

# Load documentation
doc = mock_data_loader.load_documentation("doc-001")

# Get documentation list
docs = mock_data_loader.get_documentation_list()

# Load troubleshooting data
ts_data = mock_data_loader.load_troubleshooting("sys-001")

# Get troubleshooting systems
systems = mock_data_loader.get_troubleshooting_systems()

# Clear cache
mock_data_loader.clear_cache()
```

### 4. Data Generation (`app/core/mock/generator.py`)

The data generator module creates realistic mock data:

- Generate JSON schemas for all data types
- Create mock documentation data
- Generate troubleshooting scenarios
- Create maintenance procedures
- Write data to files

**Usage Example:**

```python
from app.core.mock.generator import MockDataGenerator

generator = MockDataGenerator()

# Generate all schemas
generator.generate_all_schemas()

# Generate documentation data
generator.generate_documentation_data()

# Generate troubleshooting data
generator.generate_troubleshooting_data()

# Generate maintenance data
generator.generate_maintenance_data()

# Generate all data
generator.generate_all_data()
```

### 5. Service Layer (`app/core/mock/service.py`)

The service layer provides a high-level API for accessing mock data:

- Get documentation and search documentation
- Get troubleshooting systems and analyze troubleshooting cases
- Get maintenance aircraft types, systems, and generate procedures
- Handle errors and provide fallbacks

**Usage Example:**

```python
from app.core.mock.service import mock_data_service

# Get documentation list
docs = mock_data_service.get_documentation_list()

# Get documentation
doc = mock_data_service.get_documentation("doc-001")

# Search documentation
results = mock_data_service.search_documentation({"keywords": ["maintenance"]})

# Get troubleshooting systems
systems = mock_data_service.get_troubleshooting_systems()

# Analyze troubleshooting case
analysis = mock_data_service.analyze_troubleshooting({
    "system": "sys-001",
    "symptoms": ["sym-001", "sym-002"],
    "context": "Routine maintenance inspection"
})

# Generate maintenance procedure
procedure = mock_data_service.generate_maintenance_procedure({
    "aircraft_type": "ac-001",
    "system": "sys-001",
    "procedure_type": "proc-001",
    "parameters": {}
})
```

## Data Schemas

### Documentation Schemas

- `documentation.json`: Schema for technical documentation
- `documentation_list.json`: Schema for list of technical documentation

### Troubleshooting Schemas

- `systems.json`: Schema for aircraft systems
- `troubleshooting.json`: Schema for troubleshooting data
- `analysis.json`: Schema for troubleshooting analysis

### Maintenance Schemas

- `aircraft_types.json`: Schema for aircraft types
- `maintenance.json`: Schema for maintenance procedures

## Mock Data Generation

The mock data infrastructure includes a script for generating mock data:

```bash
# Generate all mock data
python scripts/generate_mock_data.py --all

# Generate only schemas
python scripts/generate_mock_data.py --schemas-only

# Generate only documentation data
python scripts/generate_mock_data.py --documentation

# Generate only troubleshooting data
python scripts/generate_mock_data.py --troubleshooting

# Generate only maintenance data
python scripts/generate_mock_data.py --maintenance
```

## API Integration

The mock data infrastructure is integrated with the API endpoints:

- `/api/v1/documentation/documentation`: Get documentation list
- `/api/v1/documentation/documentation/{doc_id}`: Get documentation
- `/api/v1/documentation/documentation/search`: Search documentation
- `/api/v1/troubleshooting/troubleshooting/systems`: Get troubleshooting systems
- `/api/v1/troubleshooting/troubleshooting/symptoms/{system_id}`: Get symptoms for system
- `/api/v1/troubleshooting/troubleshooting/analyze`: Analyze troubleshooting case
- `/api/v1/maintenance/maintenance/aircraft-types`: Get aircraft types
- `/api/v1/maintenance/maintenance/systems/{aircraft_id}`: Get systems for aircraft type
- `/api/v1/maintenance/maintenance/procedure-types/{aircraft_id}/{system_id}`: Get procedure types for system
- `/api/v1/maintenance/maintenance/generate`: Generate maintenance procedure

## Toggling Mock Data

The mock data infrastructure can be toggled on/off using environment variables:

```
# Enable/disable mock data globally
MOCK_DATA_USE_MOCK_DATA=true

# Enable/disable specific use cases
MOCK_DATA_ENABLE_DOCUMENTATION=true
MOCK_DATA_ENABLE_TROUBLESHOOTING=true
MOCK_DATA_ENABLE_MAINTENANCE=true

# Configure cache
MOCK_DATA_ENABLE_CACHE=true
MOCK_DATA_CACHE_TTL_SECONDS=300

# Configure schema validation
MOCK_DATA_VALIDATE_SCHEMAS=true

# Simulate latency
MOCK_DATA_SIMULATE_LATENCY=true
MOCK_DATA_MIN_LATENCY_MS=50
MOCK_DATA_MAX_LATENCY_MS=200
```

## Testing

The mock data infrastructure includes comprehensive tests:

- Schema validation tests
- Data completeness tests
- API/Utility function tests
- Integration tests
- Toggle tests

To run the tests:

```bash
# Run all tests
python -m pytest tests/test_mock_data.py

# Run specific test class
python -m pytest tests/test_mock_data.py::TestMockDataLoader

# Run specific test method
python -m pytest tests/test_mock_data.py::TestMockDataLoader::test_load_documentation
```

## Extending the Mock Data

### Adding New Documentation

1. Add a new entry to `data/mock/documentation/index.json`
2. Create a new JSON file in `data/mock/documentation/` with the document content
3. Ensure the document conforms to the documentation schema

### Adding New Troubleshooting Systems

1. Add a new entry to `data/mock/troubleshooting/systems.json`
2. Create a new JSON file in `data/mock/troubleshooting/` with the system data
3. Create a new JSON file in `data/mock/troubleshooting/` with the analysis data
4. Ensure the data conforms to the troubleshooting schemas

### Adding New Maintenance Procedures

1. Add a new entry to `data/mock/maintenance/aircraft_types.json` if needed
2. Create a new directory structure in `data/mock/maintenance/` for the aircraft type and system
3. Add procedure types and procedures
4. Ensure the data conforms to the maintenance schemas

## Performance Considerations

The mock data infrastructure includes several performance optimizations:

- Data caching with configurable TTL
- Schema caching
- Lazy loading of data
- Conditional imports for optional dependencies

## Error Handling

The mock data infrastructure includes comprehensive error handling:

- File not found errors
- Schema validation errors
- JSON parsing errors
- Missing dependency errors

## Dependencies

The mock data infrastructure has the following dependencies:

- `pyyaml`: For loading YAML files (optional)
- `jsonschema`: For schema validation (optional)

## Version History

- **v1.0.0**: Initial implementation of mock data infrastructure
- **v1.0.1**: Added support for conditional imports of optional dependencies
- **v1.0.2**: Enhanced error handling and documentation
