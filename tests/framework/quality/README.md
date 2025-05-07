# MAGPIE Response Quality Evaluation Framework

This directory contains the response quality evaluation framework for the MAGPIE platform, designed to evaluate agent responses and simulate user feedback.

## Directory Structure

- `metrics.py`: Response quality metrics for evaluating agent responses
- `reference.py`: Reference dataset for response quality evaluation
- `feedback.py`: User feedback simulation for response quality evaluation
- `pipeline.py`: Automated evaluation pipeline for response quality evaluation
- `generators.py`: Test case generators for response quality evaluation

## Quality Metrics

The quality metrics module (`metrics.py`) provides metrics for evaluating response quality:

```python
from tests.framework.quality.metrics import (
    QualityDimension, QualityScore, QualityEvaluation, QualityEvaluator,
    RelevanceMetric, AccuracyMetric, CompletenessMetric
)

# Create evaluator
evaluator = QualityEvaluator()

# Evaluate response
evaluation = evaluator.evaluate(
    query="What is the recommended tire pressure for a Boeing 737?",
    response="The recommended tire pressure for a Boeing 737-800 is 200 psi...",
    reference_data={
        "facts": {
            "main_gear_pressure": "200 psi",
            "nose_gear_pressure": "180 psi"
        },
        "required_elements": [
            "tire pressure",
            "main landing gear",
            "nose landing gear",
            "maintenance manual"
        ]
    }
)

# Print evaluation
print(f"Overall score: {evaluation.overall_score:.2f}")

for score in evaluation.scores:
    print(f"{score.dimension.value}: {score.score:.2f}/{score.max_score:.2f}")
```

## Reference Dataset

The reference dataset module (`reference.py`) provides utilities for creating and managing reference datasets:

```python
from tests.framework.quality.reference import (
    ReferenceType, ReferenceItem, ReferenceDataset, ReferenceDatasetManager
)

# Create manager
manager = ReferenceDatasetManager()

# Create dataset
dataset = manager.create_dataset("aircraft_maintenance")

# Add items
manager.add_fact("aircraft_maintenance", "main_gear_pressure", "200 psi", tags=["tire", "pressure"])
manager.add_fact("aircraft_maintenance", "nose_gear_pressure", "180 psi", tags=["tire", "pressure"])

manager.add_required_element("aircraft_maintenance", "tire pressure", tags=["tire"])
manager.add_required_element("aircraft_maintenance", "main landing gear", tags=["tire"])

# Get reference data
reference_data = manager.get_reference_data("aircraft_maintenance", tags=["tire"])
```

## User Feedback Simulation

The user feedback simulation module (`feedback.py`) provides utilities for simulating user feedback:

```python
from tests.framework.quality.feedback import (
    FeedbackType, FeedbackSentiment, UserFeedback, FeedbackGenerator, FeedbackSimulator
)

# Create simulator
simulator = FeedbackSimulator(seed=42)

# Simulate feedback
feedback_list = simulator.simulate_feedback(
    query="What is the recommended tire pressure for a Boeing 737?",
    response="The recommended tire pressure for a Boeing 737-800 is 200 psi...",
    evaluation=evaluation,
    feedback_types=[FeedbackType.RATING, FeedbackType.COMMENT]
)

# Print feedback
for feedback in feedback_list:
    print(f"{feedback.type.value}: {feedback.sentiment.value}")
    print(f"Content: {feedback.content}")

# Get statistics
stats = simulator.get_feedback_statistics()
```

## Evaluation Pipeline

The evaluation pipeline module (`pipeline.py`) provides utilities for creating and running automated evaluation pipelines:

```python
from tests.framework.quality.pipeline import (
    EvaluationStage, EvaluationResult, EvaluationPipeline,
    default_preparation_handler, default_metrics_handler,
    default_feedback_handler, default_analysis_handler,
    default_reporting_handler
)

# Create pipeline
pipeline = EvaluationPipeline(name="Example Pipeline")

# Add default stages
pipeline.add_stage(EvaluationStage.PREPARATION, default_preparation_handler)
pipeline.add_stage(EvaluationStage.METRICS, default_metrics_handler)
pipeline.add_stage(EvaluationStage.FEEDBACK, default_feedback_handler)
pipeline.add_stage(EvaluationStage.ANALYSIS, default_analysis_handler)
pipeline.add_stage(EvaluationStage.REPORTING, default_reporting_handler)

# Run evaluation
result = await pipeline.evaluate(
    query="What is the recommended tire pressure for a Boeing 737?",
    response="The recommended tire pressure for a Boeing 737-800 is 200 psi...",
    reference_dataset="aircraft_maintenance",
    reference_tags=["tire", "pressure"]
)

# Save results
pipeline.save_results()
```

## Test Case Generators

The test case generators module (`generators.py`) provides utilities for generating test cases:

```python
from tests.framework.quality.generators import (
    TestCaseType, TestCaseCategory, TestCaseDifficulty,
    TestCase, TestCaseGenerator, QualityDimensionGenerator
)

# Create generator
generator = TestCaseGenerator(seed=42)

# Generate test case
test_case = generator.generate_test_case(
    agent_type=AgentType.DOCUMENTATION,
    type=TestCaseType.STANDARD,
    category=TestCaseCategory.TECHNICAL,
    difficulty=TestCaseDifficulty.MODERATE
)

# Generate test suite
test_suite = generator.generate_test_suite(
    name="Example Test Suite",
    standard_count=5,
    edge_case_count=2,
    adversarial_count=2,
    regression_count=3,
    agent_types=[AgentType.DOCUMENTATION, AgentType.TROUBLESHOOTING]
)

# Create dimension generator
dimension_generator = QualityDimensionGenerator(seed=42)

# Generate dimensions and weights
dimensions, weights = dimension_generator.generate_weighted_dimensions(
    count=3,
    include_dimensions=[QualityDimension.RELEVANCE, QualityDimension.ACCURACY]
)
```

## Writing Quality Evaluation Tests

When writing quality evaluation tests using this framework, follow these guidelines:

1. Create a reference dataset with facts and required elements
2. Create an evaluation pipeline with appropriate stages
3. Generate test cases for different agent types and difficulty levels
4. Run the evaluation pipeline on agent responses
5. Analyze the results and simulate user feedback

Example test:

```python
import pytest
from tests.framework.quality.pipeline import EvaluationPipeline
from tests.framework.quality.generators import TestCaseGenerator

class TestAgentQuality:
    @pytest.fixture
    def evaluation_pipeline(self):
        # Create pipeline
        pipeline = EvaluationPipeline(name="Agent Quality Test")
        
        # Add default stages
        pipeline.add_stage(EvaluationStage.PREPARATION, default_preparation_handler)
        pipeline.add_stage(EvaluationStage.METRICS, default_metrics_handler)
        pipeline.add_stage(EvaluationStage.FEEDBACK, default_feedback_handler)
        pipeline.add_stage(EvaluationStage.ANALYSIS, default_analysis_handler)
        pipeline.add_stage(EvaluationStage.REPORTING, default_reporting_handler)
        
        return pipeline
    
    @pytest.fixture
    def test_case_generator(self):
        return TestCaseGenerator(seed=42)
    
    @pytest.mark.asyncio
    async def test_documentation_agent_quality(
        self, documentation_agent, evaluation_pipeline, test_case_generator
    ):
        # Generate test cases
        test_cases = test_case_generator.generate_test_cases(
            count=5,
            agent_types=[AgentType.DOCUMENTATION],
            types=[TestCaseType.STANDARD]
        )
        
        # Process each test case
        for test_case in test_cases:
            # Process query
            response = await documentation_agent.process_query(
                query=test_case.query,
                conversation_id="test-conversation"
            )
            
            # Evaluate response
            result = await evaluation_pipeline.evaluate(
                query=test_case.query,
                response=response["response"],
                reference_dataset="aircraft_maintenance"
            )
            
            # Verify quality
            assert result.evaluation.overall_score >= 7.0
```

## Running Quality Evaluation Tests

To run quality evaluation tests using this framework:

```bash
# Run all quality evaluation tests
python -m pytest tests/quality/

# Run specific test file
python -m pytest tests/quality/core/agents/test_agent_quality.py

# Run specific test class
python -m pytest tests/quality/core/agents/test_agent_quality.py::TestAgentQuality

# Run specific test method
python -m pytest tests/quality/core/agents/test_agent_quality.py::TestAgentQuality::test_documentation_agent_quality
```
