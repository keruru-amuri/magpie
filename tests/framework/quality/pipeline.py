"""
Automated evaluation pipeline for response quality evaluation.

This module provides utilities for creating and running automated evaluation pipelines.
"""
import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
from datetime import datetime
from pathlib import Path

from tests.framework.quality.metrics import (
    QualityDimension, QualityScore, QualityEvaluation, QualityEvaluator
)
from tests.framework.quality.reference import (
    ReferenceType, ReferenceItem, ReferenceDataset, ReferenceDatasetManager
)
from tests.framework.quality.feedback import (
    FeedbackType, FeedbackSentiment, UserFeedback, FeedbackSimulator
)

# Configure logging
logger = logging.getLogger(__name__)


class EvaluationStage(Enum):
    """Enum for evaluation stages."""
    PREPARATION = "preparation"
    METRICS = "metrics"
    FEEDBACK = "feedback"
    ANALYSIS = "analysis"
    REPORTING = "reporting"


class EvaluationResult:
    """
    Model for evaluation results.
    """
    
    def __init__(
        self,
        query: str,
        response: str,
        evaluation: QualityEvaluation,
        feedback: Optional[List[UserFeedback]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize evaluation result.
        
        Args:
            query: User query
            response: Agent response
            evaluation: Quality evaluation
            feedback: Optional user feedback
            metadata: Optional metadata
        """
        self.query = query
        self.response = response
        self.evaluation = evaluation
        self.feedback = feedback or []
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "query": self.query,
            "response": self.response,
            "evaluation": self.evaluation.to_dict(),
            "feedback": [feedback.to_dict() for feedback in self.feedback],
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class EvaluationPipeline:
    """
    Pipeline for automated response quality evaluation.
    """
    
    def __init__(
        self,
        name: str,
        evaluator: Optional[QualityEvaluator] = None,
        reference_manager: Optional[ReferenceDatasetManager] = None,
        feedback_simulator: Optional[FeedbackSimulator] = None,
        output_dir: Optional[Union[str, Path]] = None
    ):
        """
        Initialize evaluation pipeline.
        
        Args:
            name: Pipeline name
            evaluator: Optional quality evaluator
            reference_manager: Optional reference dataset manager
            feedback_simulator: Optional feedback simulator
            output_dir: Optional output directory
        """
        self.name = name
        self.evaluator = evaluator or QualityEvaluator()
        self.reference_manager = reference_manager or ReferenceDatasetManager()
        self.feedback_simulator = feedback_simulator or FeedbackSimulator()
        self.output_dir = output_dir or Path("evaluation_results")
        self.results = []
        self.stages = {}
        self.hooks = {}
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
    
    def add_stage(
        self,
        stage: EvaluationStage,
        handler: Callable,
        enabled: bool = True
    ):
        """
        Add a stage to the pipeline.
        
        Args:
            stage: Evaluation stage
            handler: Stage handler function
            enabled: Whether the stage is enabled
        """
        self.stages[stage] = {
            "handler": handler,
            "enabled": enabled
        }
    
    def add_hook(
        self,
        stage: EvaluationStage,
        hook: Callable,
        priority: int = 0
    ):
        """
        Add a hook to a stage.
        
        Args:
            stage: Evaluation stage
            hook: Hook function
            priority: Hook priority (higher priority hooks run first)
        """
        if stage not in self.hooks:
            self.hooks[stage] = []
        
        self.hooks[stage].append({
            "hook": hook,
            "priority": priority
        })
        
        # Sort hooks by priority (descending)
        self.hooks[stage].sort(key=lambda x: x["priority"], reverse=True)
    
    def is_stage_enabled(self, stage: EvaluationStage) -> bool:
        """
        Check if a stage is enabled.
        
        Args:
            stage: Evaluation stage
            
        Returns:
            True if enabled, False otherwise
        """
        return stage in self.stages and self.stages[stage]["enabled"]
    
    def enable_stage(self, stage: EvaluationStage):
        """
        Enable a stage.
        
        Args:
            stage: Evaluation stage
        """
        if stage in self.stages:
            self.stages[stage]["enabled"] = True
    
    def disable_stage(self, stage: EvaluationStage):
        """
        Disable a stage.
        
        Args:
            stage: Evaluation stage
        """
        if stage in self.stages:
            self.stages[stage]["enabled"] = False
    
    def run_hooks(
        self,
        stage: EvaluationStage,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run hooks for a stage.
        
        Args:
            stage: Evaluation stage
            context: Hook context
            
        Returns:
            Updated context
        """
        if stage not in self.hooks:
            return context
        
        for hook_info in self.hooks[stage]:
            hook = hook_info["hook"]
            context = hook(context)
        
        return context
    
    async def evaluate(
        self,
        query: str,
        response: str,
        reference_dataset: Optional[str] = None,
        reference_tags: Optional[List[str]] = None,
        dimensions: Optional[List[QualityDimension]] = None,
        weights: Optional[Dict[QualityDimension, float]] = None,
        feedback_types: Optional[List[FeedbackType]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """
        Evaluate response quality.
        
        Args:
            query: User query
            response: Agent response
            reference_dataset: Optional reference dataset name
            reference_tags: Optional reference tags
            dimensions: Optional list of dimensions to evaluate
            weights: Optional weights for each dimension
            feedback_types: Optional list of feedback types
            metadata: Optional metadata
            
        Returns:
            Evaluation result
        """
        # Initialize context
        context = {
            "query": query,
            "response": response,
            "reference_dataset": reference_dataset,
            "reference_tags": reference_tags,
            "dimensions": dimensions,
            "weights": weights,
            "feedback_types": feedback_types,
            "metadata": metadata or {},
            "pipeline": self
        }
        
        # Run preparation stage
        if self.is_stage_enabled(EvaluationStage.PREPARATION):
            # Run hooks
            context = self.run_hooks(EvaluationStage.PREPARATION, context)
            
            # Run handler
            handler = self.stages[EvaluationStage.PREPARATION]["handler"]
            context = handler(context)
        
        # Get reference data
        reference_data = {}
        if reference_dataset:
            reference_data = self.reference_manager.get_reference_data(
                reference_dataset,
                tags=reference_tags
            )
        
        # Run metrics stage
        evaluation = None
        if self.is_stage_enabled(EvaluationStage.METRICS):
            # Run hooks
            context = self.run_hooks(EvaluationStage.METRICS, context)
            
            # Run handler
            handler = self.stages[EvaluationStage.METRICS]["handler"]
            context = handler(context)
            
            # Get evaluation from context
            evaluation = context.get("evaluation")
        
        # Default evaluation if not provided
        if not evaluation:
            evaluation = self.evaluator.evaluate(
                query=query,
                response=response,
                reference_data=reference_data,
                dimensions=dimensions,
                weights=weights,
                metadata=metadata
            )
        
        # Run feedback stage
        feedback = []
        if self.is_stage_enabled(EvaluationStage.FEEDBACK):
            # Run hooks
            context = self.run_hooks(EvaluationStage.FEEDBACK, context)
            
            # Run handler
            handler = self.stages[EvaluationStage.FEEDBACK]["handler"]
            context = handler(context)
            
            # Get feedback from context
            feedback = context.get("feedback", [])
        
        # Default feedback if not provided
        if not feedback:
            feedback = self.feedback_simulator.simulate_feedback(
                query=query,
                response=response,
                evaluation=evaluation,
                feedback_types=feedback_types,
                metadata=metadata
            )
        
        # Create result
        result = EvaluationResult(
            query=query,
            response=response,
            evaluation=evaluation,
            feedback=feedback,
            metadata=metadata
        )
        
        # Run analysis stage
        if self.is_stage_enabled(EvaluationStage.ANALYSIS):
            # Add result to context
            context["result"] = result
            
            # Run hooks
            context = self.run_hooks(EvaluationStage.ANALYSIS, context)
            
            # Run handler
            handler = self.stages[EvaluationStage.ANALYSIS]["handler"]
            context = handler(context)
            
            # Get updated result from context
            result = context.get("result", result)
        
        # Run reporting stage
        if self.is_stage_enabled(EvaluationStage.REPORTING):
            # Add result to context
            context["result"] = result
            
            # Run hooks
            context = self.run_hooks(EvaluationStage.REPORTING, context)
            
            # Run handler
            handler = self.stages[EvaluationStage.REPORTING]["handler"]
            context = handler(context)
        
        # Add result to list
        self.results.append(result)
        
        return result
    
    async def evaluate_batch(
        self,
        queries: List[str],
        responses: List[str],
        reference_dataset: Optional[str] = None,
        reference_tags: Optional[List[str]] = None,
        dimensions: Optional[List[QualityDimension]] = None,
        weights: Optional[Dict[QualityDimension, float]] = None,
        feedback_types: Optional[List[FeedbackType]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        concurrency: int = 1
    ) -> List[EvaluationResult]:
        """
        Evaluate multiple responses.
        
        Args:
            queries: List of user queries
            responses: List of agent responses
            reference_dataset: Optional reference dataset name
            reference_tags: Optional reference tags
            dimensions: Optional list of dimensions to evaluate
            weights: Optional weights for each dimension
            feedback_types: Optional list of feedback types
            metadata: Optional metadata
            concurrency: Number of concurrent evaluations
            
        Returns:
            List of evaluation results
        """
        if len(queries) != len(responses):
            raise ValueError("Number of queries and responses must match")
        
        # Create tasks
        tasks = []
        
        for i in range(len(queries)):
            task = self.evaluate(
                query=queries[i],
                response=responses[i],
                reference_dataset=reference_dataset,
                reference_tags=reference_tags,
                dimensions=dimensions,
                weights=weights,
                feedback_types=feedback_types,
                metadata=metadata
            )
            
            tasks.append(task)
        
        # Run tasks with limited concurrency
        results = []
        
        for i in range(0, len(tasks), concurrency):
            batch = tasks[i:i+concurrency]
            batch_results = await asyncio.gather(*batch)
            results.extend(batch_results)
        
        return results
    
    def get_results(
        self,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None
    ) -> List[EvaluationResult]:
        """
        Get evaluation results.
        
        Args:
            min_score: Optional minimum overall score filter
            max_score: Optional maximum overall score filter
            
        Returns:
            List of evaluation results
        """
        if min_score is None and max_score is None:
            return self.results
        
        filtered_results = []
        
        for result in self.results:
            overall_score = result.evaluation.overall_score
            
            if overall_score is None:
                continue
            
            if min_score is not None and overall_score < min_score:
                continue
            
            if max_score is not None and overall_score > max_score:
                continue
            
            filtered_results.append(result)
        
        return filtered_results
    
    def get_average_score(self, dimension: Optional[QualityDimension] = None) -> Optional[float]:
        """
        Get average score.
        
        Args:
            dimension: Optional dimension filter
            
        Returns:
            Average score or None if no scores
        """
        if dimension:
            return self.evaluator.get_average_score(dimension)
        
        # Calculate average overall score
        scores = []
        
        for result in self.results:
            if result.evaluation.overall_score is not None:
                scores.append(result.evaluation.overall_score)
        
        if not scores:
            return None
        
        return sum(scores) / len(scores)
    
    def save_results(self, filename: Optional[str] = None):
        """
        Save evaluation results to file.
        
        Args:
            filename: Optional filename
        """
        # Generate filename
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.name.lower().replace(' ', '_')}_{timestamp}.json"
        
        # Create output path
        output_path = Path(self.output_dir) / filename
        
        # Save results
        with open(output_path, "w") as f:
            json.dump({
                "name": self.name,
                "timestamp": datetime.now().isoformat(),
                "results": [result.to_dict() for result in self.results]
            }, f, indent=2)
        
        logger.info(f"Evaluation results saved to {output_path}")
    
    def clear_results(self):
        """Clear evaluation results."""
        self.results = []


# Default stage handlers
def default_preparation_handler(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Default preparation stage handler.
    
    Args:
        context: Stage context
        
    Returns:
        Updated context
    """
    # Nothing to do by default
    return context


def default_metrics_handler(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Default metrics stage handler.
    
    Args:
        context: Stage context
        
    Returns:
        Updated context
    """
    # Get pipeline
    pipeline = context["pipeline"]
    
    # Get reference data
    reference_data = {}
    if context.get("reference_dataset"):
        reference_data = pipeline.reference_manager.get_reference_data(
            context["reference_dataset"],
            tags=context.get("reference_tags")
        )
    
    # Evaluate response
    evaluation = pipeline.evaluator.evaluate(
        query=context["query"],
        response=context["response"],
        reference_data=reference_data,
        dimensions=context.get("dimensions"),
        weights=context.get("weights"),
        metadata=context.get("metadata")
    )
    
    # Add evaluation to context
    context["evaluation"] = evaluation
    
    return context


def default_feedback_handler(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Default feedback stage handler.
    
    Args:
        context: Stage context
        
    Returns:
        Updated context
    """
    # Get pipeline
    pipeline = context["pipeline"]
    
    # Get evaluation
    evaluation = context.get("evaluation")
    
    # Simulate feedback
    feedback = pipeline.feedback_simulator.simulate_feedback(
        query=context["query"],
        response=context["response"],
        evaluation=evaluation,
        feedback_types=context.get("feedback_types"),
        metadata=context.get("metadata")
    )
    
    # Add feedback to context
    context["feedback"] = feedback
    
    return context


def default_analysis_handler(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Default analysis stage handler.
    
    Args:
        context: Stage context
        
    Returns:
        Updated context
    """
    # Nothing to do by default
    return context


def default_reporting_handler(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Default reporting stage handler.
    
    Args:
        context: Stage context
        
    Returns:
        Updated context
    """
    # Get pipeline
    pipeline = context["pipeline"]
    
    # Get result
    result = context["result"]
    
    # Log result
    logger.info(f"Evaluation result: {result.evaluation.overall_score:.2f}")
    
    return context


# Example usage
if __name__ == "__main__":
    # Create pipeline
    pipeline = EvaluationPipeline(name="Example Pipeline")
    
    # Add default stages
    pipeline.add_stage(EvaluationStage.PREPARATION, default_preparation_handler)
    pipeline.add_stage(EvaluationStage.METRICS, default_metrics_handler)
    pipeline.add_stage(EvaluationStage.FEEDBACK, default_feedback_handler)
    pipeline.add_stage(EvaluationStage.ANALYSIS, default_analysis_handler)
    pipeline.add_stage(EvaluationStage.REPORTING, default_reporting_handler)
    
    # Create reference dataset
    manager = pipeline.reference_manager
    manager.create_dataset("aircraft_maintenance")
    
    # Add reference data
    manager.add_fact("aircraft_maintenance", "main_gear_pressure", "200 psi", tags=["tire", "pressure"])
    manager.add_fact("aircraft_maintenance", "nose_gear_pressure", "180 psi", tags=["tire", "pressure"])
    
    manager.add_required_element("aircraft_maintenance", "tire pressure", tags=["tire"])
    manager.add_required_element("aircraft_maintenance", "main landing gear", tags=["tire"])
    manager.add_required_element("aircraft_maintenance", "nose landing gear", tags=["tire"])
    manager.add_required_element("aircraft_maintenance", "maintenance manual", tags=["documentation"])
    
    # Run evaluation
    async def run_evaluation():
        result = await pipeline.evaluate(
            query="What is the recommended tire pressure for a Boeing 737?",
            response="""
            The recommended tire pressure for a Boeing 737-800 is 200 psi for the main landing gear
            and 180 psi for the nose landing gear. These values may vary slightly based on the specific
            aircraft configuration and operating conditions.
            
            Always refer to the Aircraft Maintenance Manual (AMM) for the exact specifications for your
            aircraft. The tire pressure should be checked daily as part of the pre-flight inspection.
            """,
            reference_dataset="aircraft_maintenance",
            reference_tags=["tire", "pressure"]
        )
        
        # Print result
        print(f"Overall score: {result.evaluation.overall_score:.2f}")
        
        for score in result.evaluation.scores:
            print(f"{score.dimension.value}: {score.score:.2f}/{score.max_score:.2f}")
        
        # Save results
        pipeline.save_results()
    
    # Run evaluation
    asyncio.run(run_evaluation())
