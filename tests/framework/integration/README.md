# MAGPIE Integration Testing Framework

This directory contains the integration testing framework for the MAGPIE platform, designed to test interactions between system components.

## Directory Structure

- `environment.py`: Integration test environment configuration
- `harness.py`: Test harness for tracking component interactions
- `scenarios.py`: Predefined test scenarios
- `runner.py`: Test runner for executing test scenarios
- `reset.py`: Utilities for resetting system state between tests

## Integration Test Environment

The integration test environment (`environment.py`) provides a configurable environment for integration testing:

```python
from tests.framework.integration.environment import IntegrationTestEnvironment, DependencyType, DependencyMode

# Create integration test environment
env = IntegrationTestEnvironment()

# Get database dependency
db_dependency = env.get_dependency(DependencyType.DATABASE)

# Get LLM dependency
llm_dependency = env.get_dependency(DependencyType.LLM)

# Clean up
env.cleanup()
```

## Interaction Tracking

The interaction tracking harness (`harness.py`) provides utilities for tracking interactions between components:

```python
from tests.framework.integration.harness import InteractionTracker, TrackedComponent, track_class

# Create interaction tracker
tracker = InteractionTracker()

# Create tracked component
component = TrackedComponent("TestComponent", tracker)

# Define test method
@component.track_method
def test_method(x, y):
    return x + y

# Call test method
result = test_method(1, 2)

# Get interactions
interactions = tracker.get_interactions()
```

## Test Scenarios

The test scenarios module (`scenarios.py`) provides predefined test scenarios:

```python
from tests.framework.integration.scenarios import SimpleQueryScenario, MultiTurnConversationScenario

# Create simple query scenario
simple_scenario = SimpleQueryScenario(
    orchestrator=orchestrator,
    tracker=tracker,
    input_simulator=input_simulator
)

# Run simple query scenario
await simple_scenario.run()

# Create multi-turn conversation scenario
multi_turn_scenario = MultiTurnConversationScenario(
    orchestrator=orchestrator,
    tracker=tracker,
    input_simulator=input_simulator
)

# Run multi-turn conversation scenario
await multi_turn_scenario.run()
```

## Test Runner

The test runner (`runner.py`) provides utilities for running test scenarios:

```python
from tests.framework.integration.runner import TestRunner, TestSuite

# Create test runner
runner = TestRunner()

# Create test suite
suite = runner.create_suite("Example Suite", "Example test suite")

# Add scenarios
suite.add_scenario(SimpleQueryScenario(...))

# Run test suite
results = await runner.run_suite(suite)

# Clean up
runner.cleanup()
```

## System State Reset

The system state reset utilities (`reset.py`) provide utilities for resetting the system state between tests:

```python
from tests.framework.integration.reset import SystemStateResetter, DatabaseResetter, CacheResetter

# Create system state resetter
resetter = SystemStateResetter()

# Add reset functions
resetter.add_reset_function(lambda: print("Resetting database"))
resetter.add_reset_function(lambda: print("Resetting cache"))

# Reset all system state
resetter.reset_all()
```

## Writing Integration Tests

When writing integration tests using this framework, follow these guidelines:

1. Create an integration test environment with the desired configuration
2. Create test scenarios for the components you want to test
3. Use the interaction tracker to track interactions between components
4. Use the test runner to run your test scenarios
5. Use the system state reset utilities to reset the system state between tests

Example test:

```python
import pytest
from tests.framework.integration.environment import IntegrationTestEnvironment
from tests.framework.integration.harness import InteractionTracker
from tests.framework.integration.scenarios import SimpleQueryScenario
from tests.framework.integration.runner import TestRunner, TestSuite

class TestOrchestrator:
    @pytest.fixture
    def test_environment(self):
        # Create integration test environment
        env = IntegrationTestEnvironment()
        
        yield env
        
        # Clean up
        env.cleanup()
    
    @pytest.fixture
    def test_runner(self, test_environment):
        # Create test runner
        runner = TestRunner(environment=test_environment)
        
        yield runner
        
        # Clean up
        runner.cleanup()
    
    @pytest.mark.asyncio
    async def test_simple_query(self, test_runner, test_environment):
        # Get orchestrator
        orchestrator = test_environment.get_dependency("orchestrator")["orchestrator"]
        
        # Create test suite
        suite = test_runner.create_suite("Simple Query Test")
        
        # Create tracker
        tracker = InteractionTracker()
        
        # Add scenario
        suite.add_scenario(SimpleQueryScenario(
            orchestrator=orchestrator,
            tracker=tracker
        ))
        
        # Run test suite
        results = await test_runner.run_suite(suite)
        
        # Verify results
        assert len(results) == 1
        assert results[0].success
```

## Running Integration Tests

To run integration tests using this framework:

```bash
# Run all integration tests
python -m pytest tests/integration/

# Run specific test file
python -m pytest tests/integration/core/orchestrator/test_orchestrator_integration.py

# Run specific test class
python -m pytest tests/integration/core/orchestrator/test_orchestrator_integration.py::TestOrchestratorIntegration

# Run specific test method
python -m pytest tests/integration/core/orchestrator/test_orchestrator_integration.py::TestOrchestratorIntegration::test_simple_query
```
