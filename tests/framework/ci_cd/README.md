# MAGPIE CI/CD Integration and Test Data Management

This directory contains the CI/CD integration and test data management framework for the MAGPIE platform.

## Directory Structure

- `pipeline.py`: CI/CD pipeline integration for running tests
- `data_management.py`: Test data management system
- `data_generator.py`: Synthetic test data generator
- `config.py`: CI/CD configuration utilities

## CI/CD Pipeline Integration

The CI/CD pipeline integration module (`pipeline.py`) provides utilities for running tests in CI/CD pipelines:

```python
from tests.framework.ci_cd.pipeline import (
    TestType, TestStatus, TestResult, TestSuite, TestPipeline, TestSelector
)

# Create test pipeline
pipeline = TestPipeline(name="MAGPIE Tests")

# Add test suite
suite = TestSuite(
    name="Unit Tests",
    type=TestType.UNIT,
    command="python -m pytest tests/unit",
    path="tests/unit",
    timeout=300
)

pipeline.add_suite(suite)

# Run tests
results = pipeline.run_all()

# Get summary
summary = pipeline.get_summary()
print(f"Pass rate: {summary['pass_rate']:.2%}")

# Save results
pipeline.save_results()
```

## Test Data Management

The test data management module (`data_management.py`) provides utilities for managing test data:

```python
from tests.framework.ci_cd.data_management import (
    DataCategory, DataFormat, DataItem, DataSet, DataManager
)

# Create data manager
manager = DataManager()

# Create data set
data_set = manager.create_set(
    name="Aircraft Maintenance",
    description="Test data for aircraft maintenance",
    tags=["maintenance", "test"]
)

# Add items
manager.add_item(
    set_id=data_set.id,
    name="Boeing 737 Maintenance Manual",
    category=DataCategory.DOCUMENTATION,
    format=DataFormat.TEXT,
    source_path="path/to/manual.txt",
    tags=["boeing", "737", "manual"]
)

# Get items by category
documentation_items = manager.get_items_by_category(DataCategory.DOCUMENTATION)

# Get items by tag
tire_items = manager.get_items_by_tag("tire")

# Update checksums
manager.update_checksums()

# Verify checksums
invalid_items = manager.verify_checksums()
```

## Synthetic Test Data Generator

The synthetic test data generator module (`data_generator.py`) provides utilities for generating synthetic test data:

```python
from tests.framework.ci_cd.data_generator import DataGenerator
from tests.framework.ci_cd.data_management import DataManager

# Create data manager
manager = DataManager()

# Create data generator
generator = DataGenerator(data_manager=manager)

# Generate documentation data
documentation_set = generator.generate_documentation_data(count=10)

# Generate troubleshooting data
troubleshooting_set = generator.generate_troubleshooting_data(count=10)

# Generate maintenance data
maintenance_set = generator.generate_maintenance_data(count=10)

# Generate conversation data
conversation_set = generator.generate_conversation_data(count=10)

# Generate reference data
reference_set = generator.generate_reference_data()

# Generate mock data
mock_set = generator.generate_mock_data()

# Generate all data
all_data_set = generator.generate_all_data(
    documentation_count=5,
    troubleshooting_count=5,
    maintenance_count=5,
    conversation_count=5
)
```

## CI/CD Configuration

The CI/CD configuration module (`config.py`) provides utilities for configuring CI/CD pipelines:

```python
from tests.framework.ci_cd.config import CIConfig, create_default_config
from tests.framework.ci_cd.pipeline import TestType

# Create default configuration
config = create_default_config()

# Add test suite
config.add_test_suite(
    name="Security Tests",
    type=TestType.SECURITY,
    command="python -m pytest tests/security",
    path="tests/security",
    timeout=600
)

# Set threshold
config.set_threshold("pass_rate", 0.95)

# Create pipeline
pipeline = config.create_pipeline()

# Run tests
pipeline.run_all()
```

## Setting Up CI/CD Integration

To set up CI/CD integration for your project:

1. Create a CI/CD configuration file:

```python
from tests.framework.ci_cd.config import create_default_config

# Create and save default configuration
config = create_default_config()
```

2. Generate test data:

```python
from tests.framework.ci_cd.data_generator import DataGenerator
from tests.framework.ci_cd.data_management import DataManager

# Create data manager
manager = DataManager()

# Create data generator
generator = DataGenerator(data_manager=manager)

# Generate test data
generator.generate_all_data()
```

3. Run tests in CI/CD pipeline:

```python
from tests.framework.ci_cd.config import CIConfig

# Load configuration
config = CIConfig("MAGPIE CI")

# Create pipeline
pipeline = config.create_pipeline()

# Run tests
pipeline.run_all()

# Save results
pipeline.save_results()
```

## Running Tests in CI/CD

To run tests in a CI/CD pipeline:

```bash
# Run all tests
python -m tests.framework.ci_cd.run_tests

# Run specific test type
python -m tests.framework.ci_cd.run_tests --type unit

# Run with custom configuration
python -m tests.framework.ci_cd.run_tests --config path/to/config.json
```
