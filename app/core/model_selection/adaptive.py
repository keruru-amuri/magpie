"""
Adaptive model selection module for the MAGPIE platform.

This module provides functionality for adaptively selecting models
based on historical performance data and learning from past selections.
"""
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from app.core.model_selection.performance import PerformanceTracker
from app.core.model_selection.registry import get_model_registry
from app.models.agent import ModelSize
from app.models.complexity import ComplexityLevel, ComplexityScore
from app.models.model_registry import ModelCapability, ModelInfo
from app.models.performance import PerformanceMetricType

# Configure logging
logger = logging.getLogger(__name__)


class AdaptiveSelector:
    """
    Adaptive selector for model selection.
    """

    def __init__(self, performance_tracker: Optional[PerformanceTracker] = None):
        """
        Initialize adaptive selector.

        Args:
            performance_tracker: Performance tracker
        """
        self.performance_tracker = performance_tracker
        self.registry = get_model_registry()
        
        # Exploration rate (probability of trying a different model)
        self.exploration_rate = 0.1
        
        # Learning rate (how quickly to adapt to new performance data)
        self.learning_rate = 0.2
        
        # Performance weights for different metrics
        self.metric_weights = {
            PerformanceMetricType.SUCCESS_RATE: 0.4,
            PerformanceMetricType.LATENCY: 0.2,
            PerformanceMetricType.QUALITY_SCORE: 0.3,
            PerformanceMetricType.COST: 0.1
        }
        
        # Cache for model scores
        self._model_score_cache: Dict[str, Tuple[float, datetime]] = {}
        
        # Cache TTL (1 hour)
        self._cache_ttl = timedelta(hours=1)

    def select_model_adaptively(
        self,
        complexity_level: ComplexityLevel,
        required_capabilities: Set[ModelCapability],
        cost_sensitive: bool = False,
        performance_sensitive: bool = False,
        latency_sensitive: bool = False,
        explore: bool = True
    ) -> Optional[ModelInfo]:
        """
        Select a model adaptively based on historical performance.

        Args:
            complexity_level: Complexity level
            required_capabilities: Required capabilities
            cost_sensitive: Whether to prioritize cost
            performance_sensitive: Whether to prioritize performance
            latency_sensitive: Whether to prioritize latency
            explore: Whether to explore alternative models

        Returns:
            Optional[ModelInfo]: Selected model or None if no suitable model is found
        """
        if not self.performance_tracker:
            logger.warning("Cannot perform adaptive selection without performance tracker")
            return None
            
        # Get candidate models
        candidate_models = self._get_candidate_models(complexity_level, required_capabilities)
        if not candidate_models:
            logger.warning(f"No candidate models found for complexity level: {complexity_level}")
            return None
            
        # Check if we should explore
        if explore and random.random() < self.exploration_rate:
            # Randomly select a model for exploration
            logger.info("Exploring alternative model for adaptive learning")
            return random.choice(candidate_models)
            
        # Get model scores
        model_scores = self._get_model_scores(
            candidate_models,
            cost_sensitive=cost_sensitive,
            performance_sensitive=performance_sensitive,
            latency_sensitive=latency_sensitive
        )
        
        if not model_scores:
            logger.warning("No model scores available for adaptive selection")
            return candidate_models[0]
            
        # Select the model with the highest score
        selected_model_id, _ = max(model_scores.items(), key=lambda x: x[1])
        selected_model = self.registry.get_model(selected_model_id)
        
        if selected_model:
            logger.info(f"Adaptively selected model: {selected_model.name} ({selected_model.id})")
            
        return selected_model

    def update_model_weights(
        self,
        model_id: str,
        success: bool,
        latency_ms: int,
        quality_score: Optional[float] = None
    ) -> None:
        """
        Update model weights based on feedback.

        Args:
            model_id: Model ID
            success: Whether the request was successful
            latency_ms: Latency in milliseconds
            quality_score: Optional quality score
        """
        # Clear cache for the model
        if model_id in self._model_score_cache:
            del self._model_score_cache[model_id]
            
        # Update model in registry
        model = self.registry.get_model(model_id)
        if not model:
            logger.warning(f"Cannot update weights for unknown model: {model_id}")
            return
            
        # Calculate performance score
        performance_score = 0.0
        if success:
            performance_score += 0.7
            
        # Latency score (inverse of latency, normalized)
        # Assuming max latency of 5000ms
        latency_score = max(0.0, 1.0 - (latency_ms / 5000.0))
        performance_score += 0.2 * latency_score
        
        # Quality score
        if quality_score is not None:
            performance_score += 0.1 * (quality_score / 10.0)
            
        # Update model performance score with learning rate
        current_score = model.performance_score
        updated_score = (current_score * (1 - self.learning_rate)) + (performance_score * 10 * self.learning_rate)
        
        # Update model in registry
        self.registry.update_model_performance(
            model_id=model_id,
            performance_score=updated_score
        )
        
        logger.debug(f"Updated model weights for {model_id}: {current_score} -> {updated_score}")

    def _get_candidate_models(
        self,
        complexity_level: ComplexityLevel,
        required_capabilities: Set[ModelCapability]
    ) -> List[ModelInfo]:
        """
        Get candidate models based on complexity level and required capabilities.

        Args:
            complexity_level: Complexity level
            required_capabilities: Required capabilities

        Returns:
            List[ModelInfo]: List of candidate models
        """
        # Map complexity levels to model sizes
        size_map = {
            ComplexityLevel.SIMPLE: ModelSize.SMALL,
            ComplexityLevel.MEDIUM: ModelSize.MEDIUM,
            ComplexityLevel.COMPLEX: ModelSize.LARGE
        }
        
        # Get models of the appropriate size
        preferred_size = size_map.get(complexity_level, ModelSize.MEDIUM)
        models = self.registry.get_models_by_size(preferred_size)
        
        # If no models of the preferred size, try other sizes
        if not models:
            models = self.registry.get_all_models(active_only=True)
            
        # Filter by required capabilities
        if required_capabilities:
            models = [
                model for model in models
                if all(capability in model.capabilities for capability in required_capabilities)
            ]
            
        return models

    def _get_model_scores(
        self,
        models: List[ModelInfo],
        cost_sensitive: bool = False,
        performance_sensitive: bool = False,
        latency_sensitive: bool = False
    ) -> Dict[str, float]:
        """
        Get scores for models based on historical performance.

        Args:
            models: List of models
            cost_sensitive: Whether to prioritize cost
            performance_sensitive: Whether to prioritize performance
            latency_sensitive: Whether to prioritize latency

        Returns:
            Dict[str, float]: Model IDs mapped to scores
        """
        # Check cache first
        now = datetime.utcnow()
        model_scores = {}
        
        for model in models:
            # Check if score is cached and not expired
            if model.id in self._model_score_cache:
                score, timestamp = self._model_score_cache[model.id]
                if now - timestamp < self._cache_ttl:
                    model_scores[model.id] = score
                    continue
            
            # Get performance metrics
            success_rate = self.performance_tracker.get_comparative_performance(
                "day", PerformanceMetricType.SUCCESS_RATE
            ).get(model.id, 0.5)  # Default to 0.5 if no data
            
            latency = self.performance_tracker.get_comparative_performance(
                "day", PerformanceMetricType.LATENCY
            ).get(model.id, 2500.0)  # Default to 2500ms if no data
            
            quality_score = self.performance_tracker.get_comparative_performance(
                "day", PerformanceMetricType.QUALITY_SCORE
            ).get(model.id, 5.0)  # Default to 5.0 if no data
            
            cost = self.performance_tracker.get_comparative_performance(
                "day", PerformanceMetricType.COST
            ).get(model.id, 0.0)  # Default to 0.0 if no data
            
            # Normalize metrics
            normalized_latency = max(0.0, 1.0 - (latency / 5000.0))
            normalized_quality = quality_score / 10.0
            
            # Calculate cost score (inverse of cost, normalized)
            # Assuming max cost of $10 per day
            normalized_cost = max(0.0, 1.0 - (cost / 10.0))
            
            # Adjust weights based on priorities
            weights = self.metric_weights.copy()
            
            if cost_sensitive:
                weights[PerformanceMetricType.COST] = 0.4
                weights[PerformanceMetricType.SUCCESS_RATE] = 0.3
                weights[PerformanceMetricType.QUALITY_SCORE] = 0.2
                weights[PerformanceMetricType.LATENCY] = 0.1
            elif performance_sensitive:
                weights[PerformanceMetricType.QUALITY_SCORE] = 0.4
                weights[PerformanceMetricType.SUCCESS_RATE] = 0.4
                weights[PerformanceMetricType.LATENCY] = 0.1
                weights[PerformanceMetricType.COST] = 0.1
            elif latency_sensitive:
                weights[PerformanceMetricType.LATENCY] = 0.4
                weights[PerformanceMetricType.SUCCESS_RATE] = 0.3
                weights[PerformanceMetricType.QUALITY_SCORE] = 0.2
                weights[PerformanceMetricType.COST] = 0.1
                
            # Calculate weighted score
            score = (
                weights[PerformanceMetricType.SUCCESS_RATE] * success_rate +
                weights[PerformanceMetricType.LATENCY] * normalized_latency +
                weights[PerformanceMetricType.QUALITY_SCORE] * normalized_quality +
                weights[PerformanceMetricType.COST] * normalized_cost
            )
            
            # Cache the score
            self._model_score_cache[model.id] = (score, now)
            model_scores[model.id] = score
            
        return model_scores
