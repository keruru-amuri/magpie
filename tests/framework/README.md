# MAGPIE Testing Framework

This directory contains a comprehensive testing framework for the MAGPIE platform, designed to evaluate agent responses, performance, and overall system functionality.

## Directory Structure

- `assertions/`: Assertion utilities for validating agent responses
- `fixtures/`: Test fixtures for agent testing
- `generators/`: Test case generators for different agent scenarios
- `utilities/`: Test utilities for simulating user inputs and contexts

## Test Case Generator

The test case generator (`generators/agent_test_case_generator.py`) creates varied test cases for different agent scenarios based on configurable parameters:

```python
from tests.framework.generators.agent_test_case_generator import AgentTestCaseGenerator, QueryComplexity
from app.models.conversation import AgentType

# Create generator
generator = AgentTestCaseGenerator(seed=42)

# Generate test case for documentation agent
test_case = generator.generate_test_case(
    agent_type=AgentType.DOCUMENTATION,
    complexity=QueryComplexity.MODERATE,
    include_conversation_history=True,
    include_context=True
)

# Generate multiple test cases
test_cases = generator.generate_test_cases(
    count=5,
    agent_types=[AgentType.DOCUMENTATION, AgentType.TROUBLESHOOTING],
    complexities=[QueryComplexity.SIMPLE, QueryComplexity.MODERATE]
)
```

## Response Assertions

The response assertions module (`assertions/response_assertions.py`) provides utilities for validating agent responses:

```python
from tests.framework.assertions.response_assertions import ResponseAssertions

# Check if response contains expected content
contains = ResponseAssertions.assert_response_contains(
    response, "recommended tire pressure"
)

# Check if response matches pattern
matches = ResponseAssertions.assert_response_matches_pattern(
    response, r"\d+ psi"
)

# Comprehensive quality assessment
quality = ResponseAssertions.assert_response_quality(
    response,
    query="What is the tire pressure for Boeing 737?",
    expected_patterns=["pressure values", "reference to manual", "inspection frequency"]
)
```

## Input Simulator

The input simulator (`utilities/input_simulator.py`) provides utilities for simulating user inputs and contexts:

```python
from tests.framework.utilities.input_simulator import InputSimulator
from app.models.conversation import AgentType

# Create simulator
simulator = InputSimulator(seed=42)

# Generate random query
query = simulator.generate_random_query(AgentType.DOCUMENTATION)

# Generate conversation
conversation = simulator.generate_conversation(
    agent_type=AgentType.TROUBLESHOOTING,
    num_turns=2
)

# Generate agent context
context = simulator.generate_agent_context(AgentType.MAINTENANCE)
```

## Agent Fixtures

The agent fixtures module (`fixtures/agent_fixtures.py`) provides fixtures for agent testing:

```python
# In your test file
import pytest
from tests.framework.fixtures.agent_fixtures import (
    mock_llm_service, mock_documentation_service,
    documentation_agent, input_simulator
)

def test_documentation_agent(documentation_agent, input_simulator):
    # Generate test query
    query = input_simulator.generate_random_query(AgentType.DOCUMENTATION)
    
    # Generate context
    context = input_simulator.generate_agent_context(AgentType.DOCUMENTATION)
    
    # Test agent
    response = await documentation_agent.process_query(query, context=context)
    
    # Validate response
    assert ResponseAssertions.assert_response_relevance(response["response"], query)
```

## Writing Tests

When writing tests using this framework, follow these guidelines:

1. Use the test case generator to create varied test scenarios
2. Use the input simulator to create realistic user inputs and contexts
3. Use the agent fixtures to create agents with mock dependencies
4. Use the response assertions to validate agent responses

Example test:

```python
import pytest
from app.models.conversation import AgentType
from tests.framework.generators.agent_test_case_generator import AgentTestCaseGenerator, QueryComplexity
from tests.framework.assertions.response_assertions import ResponseAssertions

# Import fixtures
pytest_plugins = ["tests.framework.fixtures.agent_fixtures"]

class TestDocumentationAgent:
    @pytest.mark.asyncio
    async def test_documentation_agent_with_generated_cases(
        self, documentation_agent, input_simulator
    ):
        # Create test case generator
        generator = AgentTestCaseGenerator(seed=42)
        
        # Generate test cases
        test_cases = generator.generate_test_cases(
            count=3,
            agent_types=[AgentType.DOCUMENTATION],
            complexities=[QueryComplexity.SIMPLE, QueryComplexity.MODERATE]
        )
        
        # Test each case
        for test_case in test_cases:
            # Process query
            response = await documentation_agent.process_query(
                query=test_case["query"],
                conversation_id=test_case["id"],
                context=test_case["context"]
            )
            
            # Validate response
            quality = ResponseAssertions.assert_response_quality(
                response["response"],
                test_case["query"],
                test_case["expected_response_patterns"]
            )
            
            # Assert quality passes threshold
            assert quality["passes_threshold"]
```

## Running Tests

To run tests using this framework:

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/unit/core/agents/test_documentation_agent.py

# Run specific test class
python -m pytest tests/unit/core/agents/test_documentation_agent.py::TestDocumentationAgent

# Run specific test method
python -m pytest tests/unit/core/agents/test_documentation_agent.py::TestDocumentationAgent::test_documentation_agent_with_generated_cases
```
