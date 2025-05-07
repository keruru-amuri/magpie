"""
Model registry module for the MAGPIE platform.

This module provides functionality for registering and managing
information about available LLM models, their capabilities, and costs.
"""
import json
import logging
import os
from functools import lru_cache
from typing import Dict, List, Optional, Set

from app.core.config import settings
from app.models.agent import ModelSize
from app.models.model_registry import ModelCapability, ModelCost, ModelInfo

# Configure logging
logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Registry for managing LLM models.
    """

    def __init__(self):
        """
        Initialize model registry.
        """
        self._models: Dict[str, ModelInfo] = {}
        self._initialized = False
        
        # Initialize default models
        self._initialize_default_models()

    def _initialize_default_models(self) -> None:
        """
        Initialize default models.
        """
        # GPT-4.1 (Large)
        self.register_model(
            id="gpt-4.1",
            name="GPT-4.1",
            size=ModelSize.LARGE,
            description="Azure OpenAI GPT-4.1 - Full capability model for complex tasks",
            max_tokens=128000,
            capabilities={
                ModelCapability.BASIC_COMPLETION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.REASONING,
                ModelCapability.SUMMARIZATION,
                ModelCapability.CLASSIFICATION,
                ModelCapability.SPECIALIZED_KNOWLEDGE,
                ModelCapability.LONG_CONTEXT
            },
            cost=ModelCost(
                input_cost_per_1k_tokens=0.01,
                output_cost_per_1k_tokens=0.03
            )
        )
        
        # GPT-4.1-mini (Medium)
        self.register_model(
            id="gpt-4.1-mini",
            name="GPT-4.1 Mini",
            size=ModelSize.MEDIUM,
            description="Azure OpenAI GPT-4.1 Mini - Balanced model for most tasks",
            max_tokens=128000,
            capabilities={
                ModelCapability.BASIC_COMPLETION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.REASONING,
                ModelCapability.SUMMARIZATION,
                ModelCapability.CLASSIFICATION,
                ModelCapability.SPECIALIZED_KNOWLEDGE,
                ModelCapability.LONG_CONTEXT
            },
            cost=ModelCost(
                input_cost_per_1k_tokens=0.003,
                output_cost_per_1k_tokens=0.006
            )
        )
        
        # GPT-4.1-nano (Small)
        self.register_model(
            id="gpt-4.1-nano",
            name="GPT-4.1 Nano",
            size=ModelSize.SMALL,
            description="Azure OpenAI GPT-4.1 Nano - Efficient model for simple tasks",
            max_tokens=128000,
            capabilities={
                ModelCapability.BASIC_COMPLETION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.SUMMARIZATION,
                ModelCapability.CLASSIFICATION
            },
            cost=ModelCost(
                input_cost_per_1k_tokens=0.0005,
                output_cost_per_1k_tokens=0.0015
            )
        )
        
        self._initialized = True
        logger.info(f"Model registry initialized with {len(self._models)} default models")

    def register_model(
        self,
        id: str,
        name: str,
        size: ModelSize,
        description: str,
        max_tokens: int,
        capabilities: Set[ModelCapability],
        cost: ModelCost,
        is_active: bool = True,
        performance_score: float = 0.0,
        success_rate: float = 0.0,
        average_latency: float = 0.0,
        additional_info: Optional[Dict[str, str]] = None
    ) -> ModelInfo:
        """
        Register a model with the registry.
        
        Args:
            id: Model ID
            name: Model name
            size: Model size
            description: Model description
            max_tokens: Maximum tokens
            capabilities: Model capabilities
            cost: Model cost
            is_active: Whether the model is active
            performance_score: Performance score
            success_rate: Success rate
            average_latency: Average latency
            additional_info: Additional information
            
        Returns:
            ModelInfo: Registered model information
        """
        model_info = ModelInfo(
            id=id,
            name=name,
            size=size,
            description=description,
            max_tokens=max_tokens,
            capabilities=capabilities,
            cost=cost,
            is_active=is_active,
            performance_score=performance_score,
            success_rate=success_rate,
            average_latency=average_latency,
            additional_info=additional_info or {}
        )
        
        self._models[id] = model_info
        logger.info(f"Registered model: {name} ({id})")
        
        return model_info

    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get model information by ID.
        
        Args:
            model_id: Model ID
            
        Returns:
            Optional[ModelInfo]: Model information or None if not found
        """
        return self._models.get(model_id)

    def get_models_by_size(self, size: ModelSize) -> List[ModelInfo]:
        """
        Get models by size.
        
        Args:
            size: Model size
            
        Returns:
            List[ModelInfo]: List of models with the specified size
        """
        return [model for model in self._models.values() if model.size == size and model.is_active]

    def get_models_by_capability(self, capability: ModelCapability) -> List[ModelInfo]:
        """
        Get models by capability.
        
        Args:
            capability: Model capability
            
        Returns:
            List[ModelInfo]: List of models with the specified capability
        """
        return [
            model for model in self._models.values() 
            if capability in model.capabilities and model.is_active
        ]

    def get_all_models(self, active_only: bool = True) -> List[ModelInfo]:
        """
        Get all models.
        
        Args:
            active_only: Whether to return only active models
            
        Returns:
            List[ModelInfo]: List of all models
        """
        if active_only:
            return [model for model in self._models.values() if model.is_active]
        return list(self._models.values())

    def update_model_performance(
        self,
        model_id: str,
        performance_score: Optional[float] = None,
        success_rate: Optional[float] = None,
        average_latency: Optional[float] = None
    ) -> bool:
        """
        Update model performance metrics.
        
        Args:
            model_id: Model ID
            performance_score: Performance score
            success_rate: Success rate
            average_latency: Average latency
            
        Returns:
            bool: True if the model was updated, False otherwise
        """
        model = self.get_model(model_id)
        if not model:
            logger.warning(f"Cannot update performance for unknown model: {model_id}")
            return False
            
        if performance_score is not None:
            model.performance_score = performance_score
            
        if success_rate is not None:
            model.success_rate = success_rate
            
        if average_latency is not None:
            model.average_latency = average_latency
            
        logger.debug(f"Updated performance metrics for model: {model_id}")
        return True

    def deactivate_model(self, model_id: str) -> bool:
        """
        Deactivate a model.
        
        Args:
            model_id: Model ID
            
        Returns:
            bool: True if the model was deactivated, False otherwise
        """
        model = self.get_model(model_id)
        if not model:
            logger.warning(f"Cannot deactivate unknown model: {model_id}")
            return False
            
        model.is_active = False
        logger.info(f"Deactivated model: {model_id}")
        return True

    def activate_model(self, model_id: str) -> bool:
        """
        Activate a model.
        
        Args:
            model_id: Model ID
            
        Returns:
            bool: True if the model was activated, False otherwise
        """
        model = self.get_model(model_id)
        if not model:
            logger.warning(f"Cannot activate unknown model: {model_id}")
            return False
            
        model.is_active = True
        logger.info(f"Activated model: {model_id}")
        return True

    def get_model_by_deployment_name(self, deployment_name: str) -> Optional[ModelInfo]:
        """
        Get model by Azure OpenAI deployment name.
        
        Args:
            deployment_name: Deployment name
            
        Returns:
            Optional[ModelInfo]: Model information or None if not found
        """
        # Map deployment names to model IDs
        deployment_map = {
            settings.GPT_4_1_DEPLOYMENT_NAME: "gpt-4.1",
            settings.GPT_4_1_MINI_DEPLOYMENT_NAME: "gpt-4.1-mini",
            settings.GPT_4_1_NANO_DEPLOYMENT_NAME: "gpt-4.1-nano"
        }
        
        model_id = deployment_map.get(deployment_name)
        if not model_id:
            return None
            
        return self.get_model(model_id)


@lru_cache()
def get_model_registry() -> ModelRegistry:
    """
    Get the model registry.
    
    Returns:
        ModelRegistry: Model registry
    """
    return ModelRegistry()
