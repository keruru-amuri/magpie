"""
Model registry models for the MAGPIE platform.

This module provides data models for representing and managing
information about available LLM models, their capabilities, and costs.
"""
from enum import Enum
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field

from app.models.agent import ModelSize


class ModelCapability(str, Enum):
    """
    Enum for model capabilities.
    """
    BASIC_COMPLETION = "basic_completion"
    CHAT_COMPLETION = "chat_completion"
    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    SPECIALIZED_KNOWLEDGE = "specialized_knowledge"
    LONG_CONTEXT = "long_context"


class ModelCost(BaseModel):
    """
    Model for representing model costs.
    """
    input_cost_per_1k_tokens: float
    output_cost_per_1k_tokens: float
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate the cost for a given number of tokens.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            float: Cost in USD
        """
        input_cost = (input_tokens / 1000) * self.input_cost_per_1k_tokens
        output_cost = (output_tokens / 1000) * self.output_cost_per_1k_tokens
        return input_cost + output_cost


class ModelInfo(BaseModel):
    """
    Model for storing information about an LLM model.
    """
    id: str
    name: str
    size: ModelSize
    description: str
    max_tokens: int
    capabilities: Set[ModelCapability]
    cost: ModelCost
    is_active: bool = True
    performance_score: float = 0.0
    success_rate: float = 0.0
    average_latency: float = 0.0
    additional_info: Optional[Dict[str, str]] = None
    
    def supports_capability(self, capability: ModelCapability) -> bool:
        """
        Check if the model supports a specific capability.
        
        Args:
            capability: Capability to check
            
        Returns:
            bool: True if the model supports the capability
        """
        return capability in self.capabilities
    
    def get_capability_score(self, capability: ModelCapability) -> float:
        """
        Get the capability score for a specific capability.
        
        Args:
            capability: Capability to get score for
            
        Returns:
            float: Capability score (0.0-1.0)
        """
        # Default capability scores based on model size
        default_scores = {
            ModelSize.SMALL: {
                ModelCapability.BASIC_COMPLETION: 0.8,
                ModelCapability.CHAT_COMPLETION: 0.7,
                ModelCapability.CODE_GENERATION: 0.5,
                ModelCapability.REASONING: 0.4,
                ModelCapability.SUMMARIZATION: 0.6,
                ModelCapability.CLASSIFICATION: 0.7,
                ModelCapability.SPECIALIZED_KNOWLEDGE: 0.3,
                ModelCapability.LONG_CONTEXT: 0.3
            },
            ModelSize.MEDIUM: {
                ModelCapability.BASIC_COMPLETION: 0.9,
                ModelCapability.CHAT_COMPLETION: 0.8,
                ModelCapability.CODE_GENERATION: 0.7,
                ModelCapability.REASONING: 0.7,
                ModelCapability.SUMMARIZATION: 0.8,
                ModelCapability.CLASSIFICATION: 0.8,
                ModelCapability.SPECIALIZED_KNOWLEDGE: 0.6,
                ModelCapability.LONG_CONTEXT: 0.6
            },
            ModelSize.LARGE: {
                ModelCapability.BASIC_COMPLETION: 1.0,
                ModelCapability.CHAT_COMPLETION: 1.0,
                ModelCapability.CODE_GENERATION: 0.9,
                ModelCapability.REASONING: 0.9,
                ModelCapability.SUMMARIZATION: 0.9,
                ModelCapability.CLASSIFICATION: 0.9,
                ModelCapability.SPECIALIZED_KNOWLEDGE: 0.9,
                ModelCapability.LONG_CONTEXT: 0.9
            }
        }
        
        if capability not in self.capabilities:
            return 0.0
            
        return default_scores.get(self.size, {}).get(capability, 0.5)
