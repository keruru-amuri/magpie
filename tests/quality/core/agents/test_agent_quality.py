"""
Quality evaluation tests for agents.

This module contains quality evaluation tests for agent responses.
"""
import pytest
import asyncio
import os
from typing import Dict, List, Any

from app.models.conversation import AgentType
from app.models.agent import ModelSize

from tests.framework.quality.metrics import (
    QualityDimension, QualityScore, QualityEvaluation, QualityEvaluator
)
from tests.framework.quality.reference import (
    ReferenceType, ReferenceItem, ReferenceDataset, ReferenceDatasetManager
)
from tests.framework.quality.feedback import (
    FeedbackType, FeedbackSentiment, UserFeedback, FeedbackSimulator
)
from tests.framework.quality.pipeline import (
    EvaluationStage, EvaluationResult, EvaluationPipeline,
    default_preparation_handler, default_metrics_handler,
    default_feedback_handler, default_analysis_handler,
    default_reporting_handler
)
from tests.framework.quality.generators import (
    TestCaseType, TestCaseCategory, TestCaseDifficulty,
    TestCase, TestCaseGenerator, QualityDimensionGenerator
)

# Import fixtures
pytest_plugins = ["tests.conftest_agent", "tests.conftest_orchestrator"]


class TestAgentQuality:
    """
    Quality evaluation tests for agents.
    """
    
    @pytest.fixture
    def reference_manager(self, tmp_path):
        """
        Create reference dataset manager.
        
        Args:
            tmp_path: Temporary path
            
        Returns:
            ReferenceDatasetManager: Reference dataset manager
        """
        # Create data directory
        data_dir = tmp_path / "reference_data"
        os.makedirs(data_dir, exist_ok=True)
        
        # Create manager
        manager = ReferenceDatasetManager(data_dir=data_dir)
        
        # Create dataset
        manager.create_dataset("aircraft_maintenance")
        
        # Add items
        manager.add_fact("aircraft_maintenance", "main_gear_pressure", "200 psi", tags=["tire", "pressure"])
        manager.add_fact("aircraft_maintenance", "nose_gear_pressure", "180 psi", tags=["tire", "pressure"])
        
        manager.add_required_element("aircraft_maintenance", "tire pressure", tags=["tire"])
        manager.add_required_element("aircraft_maintenance", "main landing gear", tags=["tire"])
        manager.add_required_element("aircraft_maintenance", "nose landing gear", tags=["tire"])
        manager.add_required_element("aircraft_maintenance", "maintenance manual", tags=["documentation"])
        
        manager.add_query_response(
            "aircraft_maintenance",
            "What is the recommended tire pressure for a Boeing 737?",
            """
            The recommended tire pressure for a Boeing 737-800 is 200 psi for the main landing gear
            and 180 psi for the nose landing gear. These values may vary slightly based on the specific
            aircraft configuration and operating conditions.
            
            Always refer to the Aircraft Maintenance Manual (AMM) for the exact specifications for your
            aircraft. The tire pressure should be checked daily as part of the pre-flight inspection.
            """,
            tags=["tire", "pressure"]
        )
        
        return manager
    
    @pytest.fixture
    def evaluation_pipeline(self, tmp_path, reference_manager):
        """
        Create evaluation pipeline.
        
        Args:
            tmp_path: Temporary path
            reference_manager: Reference dataset manager
            
        Returns:
            EvaluationPipeline: Evaluation pipeline
        """
        # Create output directory
        output_dir = tmp_path / "evaluation_results"
        os.makedirs(output_dir, exist_ok=True)
        
        # Create pipeline
        pipeline = EvaluationPipeline(
            name="Agent Quality Test",
            reference_manager=reference_manager,
            output_dir=output_dir
        )
        
        # Add default stages
        pipeline.add_stage(EvaluationStage.PREPARATION, default_preparation_handler)
        pipeline.add_stage(EvaluationStage.METRICS, default_metrics_handler)
        pipeline.add_stage(EvaluationStage.FEEDBACK, default_feedback_handler)
        pipeline.add_stage(EvaluationStage.ANALYSIS, default_analysis_handler)
        pipeline.add_stage(EvaluationStage.REPORTING, default_reporting_handler)
        
        return pipeline
    
    @pytest.fixture
    def test_case_generator(self):
        """
        Create test case generator.
        
        Returns:
            TestCaseGenerator: Test case generator
        """
        return TestCaseGenerator(seed=42)
    
    @pytest.fixture
    def dimension_generator(self):
        """
        Create quality dimension generator.
        
        Returns:
            QualityDimensionGenerator: Quality dimension generator
        """
        return QualityDimensionGenerator(seed=42)
    
    @pytest.mark.asyncio
    async def test_documentation_agent_quality(
        self,
        documentation_agent,
        evaluation_pipeline,
        test_case_generator
    ):
        """
        Test documentation agent quality.
        
        Args:
            documentation_agent: Documentation agent
            evaluation_pipeline: Evaluation pipeline
            test_case_generator: Test case generator
        """
        # Generate test cases
        test_cases = test_case_generator.generate_test_cases(
            count=3,
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
            assert result.evaluation.overall_score is not None
            
            # Verify feedback
            assert len(result.feedback) > 0
    
    @pytest.mark.asyncio
    async def test_troubleshooting_agent_quality(
        self,
        troubleshooting_agent,
        evaluation_pipeline,
        test_case_generator
    ):
        """
        Test troubleshooting agent quality.
        
        Args:
            troubleshooting_agent: Troubleshooting agent
            evaluation_pipeline: Evaluation pipeline
            test_case_generator: Test case generator
        """
        # Generate test cases
        test_cases = test_case_generator.generate_test_cases(
            count=3,
            agent_types=[AgentType.TROUBLESHOOTING],
            types=[TestCaseType.STANDARD]
        )
        
        # Process each test case
        for test_case in test_cases:
            # Process query
            response = await troubleshooting_agent.process_query(
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
            assert result.evaluation.overall_score is not None
            
            # Verify feedback
            assert len(result.feedback) > 0
    
    @pytest.mark.asyncio
    async def test_maintenance_agent_quality(
        self,
        maintenance_agent,
        evaluation_pipeline,
        test_case_generator
    ):
        """
        Test maintenance agent quality.
        
        Args:
            maintenance_agent: Maintenance agent
            evaluation_pipeline: Evaluation pipeline
            test_case_generator: Test case generator
        """
        # Generate test cases
        test_cases = test_case_generator.generate_test_cases(
            count=3,
            agent_types=[AgentType.MAINTENANCE],
            types=[TestCaseType.STANDARD]
        )
        
        # Process each test case
        for test_case in test_cases:
            # Process query
            response = await maintenance_agent.process_query(
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
            assert result.evaluation.overall_score is not None
            
            # Verify feedback
            assert len(result.feedback) > 0
    
    @pytest.mark.asyncio
    async def test_agent_quality_with_dimensions(
        self,
        documentation_agent,
        evaluation_pipeline,
        test_case_generator,
        dimension_generator
    ):
        """
        Test agent quality with specific dimensions.
        
        Args:
            documentation_agent: Documentation agent
            evaluation_pipeline: Evaluation pipeline
            test_case_generator: Test case generator
            dimension_generator: Quality dimension generator
        """
        # Generate dimensions and weights
        dimensions, weights = dimension_generator.generate_weighted_dimensions(
            count=3,
            include_dimensions=[QualityDimension.RELEVANCE, QualityDimension.CLARITY]
        )
        
        # Generate test case
        test_case = test_case_generator.generate_test_case(
            agent_type=AgentType.DOCUMENTATION,
            type=TestCaseType.STANDARD
        )
        
        # Process query
        response = await documentation_agent.process_query(
            query=test_case.query,
            conversation_id="test-conversation"
        )
        
        # Evaluate response
        result = await evaluation_pipeline.evaluate(
            query=test_case.query,
            response=response["response"],
            reference_dataset="aircraft_maintenance",
            dimensions=dimensions,
            weights=weights
        )
        
        # Verify quality
        assert result.evaluation.overall_score is not None
        
        # Verify dimensions
        for dimension in dimensions:
            assert result.evaluation.get_score(dimension) is not None
    
    @pytest.mark.asyncio
    async def test_agent_quality_with_feedback_types(
        self,
        documentation_agent,
        evaluation_pipeline,
        test_case_generator
    ):
        """
        Test agent quality with specific feedback types.
        
        Args:
            documentation_agent: Documentation agent
            evaluation_pipeline: Evaluation pipeline
            test_case_generator: Test case generator
        """
        # Generate test case
        test_case = test_case_generator.generate_test_case(
            agent_type=AgentType.DOCUMENTATION,
            type=TestCaseType.STANDARD
        )
        
        # Process query
        response = await documentation_agent.process_query(
            query=test_case.query,
            conversation_id="test-conversation"
        )
        
        # Evaluate response
        result = await evaluation_pipeline.evaluate(
            query=test_case.query,
            response=response["response"],
            reference_dataset="aircraft_maintenance",
            feedback_types=[FeedbackType.RATING, FeedbackType.COMMENT]
        )
        
        # Verify feedback
        assert len(result.feedback) > 0
        
        # Verify feedback types
        feedback_types = [feedback.type for feedback in result.feedback]
        assert FeedbackType.RATING in feedback_types
        assert FeedbackType.COMMENT in feedback_types
    
    @pytest.mark.asyncio
    async def test_agent_quality_with_edge_cases(
        self,
        documentation_agent,
        evaluation_pipeline,
        test_case_generator
    ):
        """
        Test agent quality with edge cases.
        
        Args:
            documentation_agent: Documentation agent
            evaluation_pipeline: Evaluation pipeline
            test_case_generator: Test case generator
        """
        # Generate edge case
        edge_case = test_case_generator.generate_edge_case(
            agent_type=AgentType.DOCUMENTATION
        )
        
        # Process query
        response = await documentation_agent.process_query(
            query=edge_case.query,
            conversation_id="test-conversation"
        )
        
        # Evaluate response
        result = await evaluation_pipeline.evaluate(
            query=edge_case.query,
            response=response["response"],
            reference_dataset="aircraft_maintenance"
        )
        
        # Verify quality
        assert result.evaluation.overall_score is not None
    
    @pytest.mark.asyncio
    async def test_agent_quality_with_adversarial_cases(
        self,
        documentation_agent,
        evaluation_pipeline,
        test_case_generator
    ):
        """
        Test agent quality with adversarial cases.
        
        Args:
            documentation_agent: Documentation agent
            evaluation_pipeline: Evaluation pipeline
            test_case_generator: Test case generator
        """
        # Generate adversarial case
        adversarial_case = test_case_generator.generate_adversarial_case(
            agent_type=AgentType.DOCUMENTATION
        )
        
        # Process query
        response = await documentation_agent.process_query(
            query=adversarial_case.query,
            conversation_id="test-conversation"
        )
        
        # Evaluate response
        result = await evaluation_pipeline.evaluate(
            query=adversarial_case.query,
            response=response["response"],
            reference_dataset="aircraft_maintenance"
        )
        
        # Verify quality
        assert result.evaluation.overall_score is not None
        
        # Verify safety score
        safety_score = result.evaluation.get_score(QualityDimension.SAFETY)
        if safety_score:
            assert safety_score.score > 0
    
    @pytest.mark.asyncio
    async def test_agent_quality_batch_evaluation(
        self,
        documentation_agent,
        evaluation_pipeline,
        test_case_generator
    ):
        """
        Test agent quality batch evaluation.
        
        Args:
            documentation_agent: Documentation agent
            evaluation_pipeline: Evaluation pipeline
            test_case_generator: Test case generator
        """
        # Generate test cases
        test_cases = test_case_generator.generate_test_cases(
            count=3,
            agent_types=[AgentType.DOCUMENTATION],
            types=[TestCaseType.STANDARD]
        )
        
        # Process queries
        queries = [test_case.query for test_case in test_cases]
        responses = []
        
        for query in queries:
            response = await documentation_agent.process_query(
                query=query,
                conversation_id="test-conversation"
            )
            
            responses.append(response["response"])
        
        # Evaluate responses
        results = await evaluation_pipeline.evaluate_batch(
            queries=queries,
            responses=responses,
            reference_dataset="aircraft_maintenance",
            concurrency=2
        )
        
        # Verify results
        assert len(results) == len(queries)
        
        for result in results:
            assert result.evaluation.overall_score is not None
            assert len(result.feedback) > 0
        
        # Save results
        evaluation_pipeline.save_results()
        
        # Get average score
        avg_score = evaluation_pipeline.get_average_score()
        assert avg_score is not None
