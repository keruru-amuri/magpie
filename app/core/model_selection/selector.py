"""
Model selector module for the MAGPIE platform.

This module provides functionality for selecting the appropriate LLM model
based on task complexity, cost considerations, and performance requirements.
"""
import logging
from typing import Dict, List, Optional, Set, Tuple

from app.core.model_selection.complexity import ComplexityAnalyzer
from app.core.model_selection.registry import get_model_registry
from app.models.agent import ModelSize
from app.models.complexity import ComplexityLevel, ComplexityScore
from app.models.model_registry import ModelCapability, ModelInfo

# Configure logging
logger = logging.getLogger(__name__)


class ModelSelector:
    """
    Selector for choosing the appropriate LLM model.
    """

    def __init__(self, complexity_analyzer: Optional[ComplexityAnalyzer] = None):
        """
        Initialize model selector.

        Args:
            complexity_analyzer: Complexity analyzer
        """
        self.complexity_analyzer = complexity_analyzer or ComplexityAnalyzer()
        self.registry = get_model_registry()
        
        # Default capability requirements for different complexity levels
        self.default_capability_requirements = {
            ComplexityLevel.SIMPLE: {
                ModelCapability.BASIC_COMPLETION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.CLASSIFICATION
            },
            ComplexityLevel.MEDIUM: {
                ModelCapability.BASIC_COMPLETION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.CLASSIFICATION,
                ModelCapability.SUMMARIZATION,
                ModelCapability.REASONING
            },
            ComplexityLevel.COMPLEX: {
                ModelCapability.BASIC_COMPLETION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.CLASSIFICATION,
                ModelCapability.SUMMARIZATION,
                ModelCapability.REASONING,
                ModelCapability.SPECIALIZED_KNOWLEDGE,
                ModelCapability.CODE_GENERATION,
                ModelCapability.LONG_CONTEXT
            }
        }

    async def select_model(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        required_capabilities: Optional[Set[ModelCapability]] = None,
        cost_sensitive: bool = False,
        performance_sensitive: bool = False,
        latency_sensitive: bool = False,
        fallback_to_smaller: bool = True
    ) -> Tuple[ModelInfo, ComplexityScore]:
        """
        Select the appropriate model for a query.

        Args:
            query: User query
            conversation_history: Optional conversation history
            required_capabilities: Optional set of required capabilities
            cost_sensitive: Whether to prioritize cost over performance
            performance_sensitive: Whether to prioritize performance over cost
            latency_sensitive: Whether to prioritize latency
            fallback_to_smaller: Whether to fallback to smaller models if needed

        Returns:
            Tuple[ModelInfo, ComplexityScore]: Selected model and complexity score

        Raises:
            ValueError: If no suitable model is found
        """
        # Analyze complexity
        complexity_score = await self.complexity_analyzer.analyze_complexity(
            query=query,
            conversation_history=conversation_history
        )
        
        logger.debug(f"Complexity analysis: {complexity_score.level} (score: {complexity_score.overall_score})")
        
        # Determine required capabilities based on complexity
        capabilities = required_capabilities or self.default_capability_requirements.get(
            complexity_score.level, self.default_capability_requirements[ComplexityLevel.MEDIUM]
        )
        
        # Get candidate models based on complexity level
        candidate_models = self._get_candidate_models(complexity_score.level, capabilities)
        
        if not candidate_models:
            logger.warning(f"No models found for complexity level: {complexity_score.level}")
            if fallback_to_smaller and complexity_score.level != ComplexityLevel.SIMPLE:
                # Try with a lower complexity level
                fallback_level = ComplexityLevel.MEDIUM if complexity_score.level == ComplexityLevel.COMPLEX else ComplexityLevel.SIMPLE
                logger.info(f"Falling back to {fallback_level} complexity level")
                candidate_models = self._get_candidate_models(fallback_level, capabilities)
                
        if not candidate_models:
            # If still no models, get all active models as a last resort
            logger.warning("No suitable models found, using all active models")
            candidate_models = self.registry.get_all_models(active_only=True)
            
        if not candidate_models:
            raise ValueError("No active models available for selection")
            
        # Rank models based on criteria
        ranked_models = self._rank_models(
            models=candidate_models,
            complexity_score=complexity_score,
            cost_sensitive=cost_sensitive,
            performance_sensitive=performance_sensitive,
            latency_sensitive=latency_sensitive
        )
        
        # Select the top-ranked model
        selected_model = ranked_models[0]
        
        logger.info(f"Selected model: {selected_model.name} ({selected_model.id}) for complexity level: {complexity_score.level}")
        
        return selected_model, complexity_score

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
        
        # Filter by required capabilities
        if required_capabilities:
            models = [
                model for model in models
                if all(capability in model.capabilities for capability in required_capabilities)
            ]
            
        return models

    def _rank_models(
        self,
        models: List[ModelInfo],
        complexity_score: ComplexityScore,
        cost_sensitive: bool = False,
        performance_sensitive: bool = False,
        latency_sensitive: bool = False
    ) -> List[ModelInfo]:
        """
        Rank models based on criteria.

        Args:
            models: List of models to rank
            complexity_score: Complexity score
            cost_sensitive: Whether to prioritize cost over performance
            performance_sensitive: Whether to prioritize performance over cost
            latency_sensitive: Whether to prioritize latency

        Returns:
            List[ModelInfo]: Ranked list of models
        """
        # Define weights for different criteria
        weights = {
            "capability": 0.4,
            "performance": 0.3,
            "cost": 0.2,
            "latency": 0.1
        }
        
        # Adjust weights based on priorities
        if cost_sensitive:
            weights["cost"] = 0.5
            weights["performance"] = 0.2
            weights["capability"] = 0.2
            weights["latency"] = 0.1
        elif performance_sensitive:
            weights["performance"] = 0.5
            weights["capability"] = 0.3
            weights["cost"] = 0.1
            weights["latency"] = 0.1
        elif latency_sensitive:
            weights["latency"] = 0.4
            weights["capability"] = 0.3
            weights["performance"] = 0.2
            weights["cost"] = 0.1
            
        # Calculate scores for each model
        model_scores = []
        for model in models:
            # Capability score
            capability_score = 0.0
            for dimension, score in complexity_score.dimension_scores.items():
                if dimension.name == "REASONING_DEPTH" and ModelCapability.REASONING in model.capabilities:
                    capability_score += score * 0.3
                elif dimension.name == "SPECIALIZED_KNOWLEDGE" and ModelCapability.SPECIALIZED_KNOWLEDGE in model.capabilities:
                    capability_score += score * 0.3
                elif dimension.name == "OUTPUT_STRUCTURE" and ModelCapability.SUMMARIZATION in model.capabilities:
                    capability_score += score * 0.2
                elif dimension.name == "CONTEXT_DEPENDENCY" and ModelCapability.LONG_CONTEXT in model.capabilities:
                    capability_score += score * 0.2
            
            capability_score = min(1.0, capability_score / 10.0)
            
            # Performance score (normalized)
            performance_score = model.performance_score / 10.0 if model.performance_score > 0 else 0.5
            
            # Cost score (inverse of cost, normalized)
            # Assuming max cost of $0.03 per token
            cost_per_token = (model.cost.input_cost_per_1k_tokens + model.cost.output_cost_per_1k_tokens) / 2
            cost_score = 1.0 - (cost_per_token / 0.03)
            
            # Latency score (inverse of latency, normalized)
            # Assuming max latency of 5 seconds
            latency_score = 1.0 - (model.average_latency / 5.0) if model.average_latency > 0 else 0.5
            
            # Calculate weighted score
            weighted_score = (
                weights["capability"] * capability_score +
                weights["performance"] * performance_score +
                weights["cost"] * cost_score +
                weights["latency"] * latency_score
            )
            
            model_scores.append((model, weighted_score))
            
        # Sort models by score (descending)
        model_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [model for model, _ in model_scores]

    def get_model_by_size(self, size: ModelSize) -> ModelInfo:
        """
        Get a model by size.

        Args:
            size: Model size

        Returns:
            ModelInfo: Model information

        Raises:
            ValueError: If no model is found for the specified size
        """
        models = self.registry.get_models_by_size(size)
        if not models:
            raise ValueError(f"No active models found for size: {size}")
            
        # Return the first model (they should be equivalent for the same size)
        return models[0]

    def get_model_deployment_name(self, model_id: str) -> str:
        """
        Get the deployment name for a model.

        Args:
            model_id: Model ID

        Returns:
            str: Deployment name

        Raises:
            ValueError: If the model is not found
        """
        from app.core.config import settings
        
        model = self.registry.get_model(model_id)
        if not model:
            raise ValueError(f"Model not found: {model_id}")
            
        # Map model sizes to deployment names
        deployment_map = {
            ModelSize.SMALL: settings.GPT_4_1_NANO_DEPLOYMENT_NAME,
            ModelSize.MEDIUM: settings.GPT_4_1_MINI_DEPLOYMENT_NAME,
            ModelSize.LARGE: settings.GPT_4_1_DEPLOYMENT_NAME
        }
        
        return deployment_map.get(model.size, settings.GPT_4_1_DEPLOYMENT_NAME)
