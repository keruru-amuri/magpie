"""
Complexity models for the MAGPIE platform.

This module provides data models for representing and analyzing
the complexity of user requests to inform model selection.
"""
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ComplexityDimension(str, Enum):
    """
    Enum for complexity dimensions.
    """
    TOKEN_COUNT = "token_count"
    REASONING_DEPTH = "reasoning_depth"
    SPECIALIZED_KNOWLEDGE = "specialized_knowledge"
    CONTEXT_DEPENDENCY = "context_dependency"
    OUTPUT_STRUCTURE = "output_structure"


class ComplexityLevel(str, Enum):
    """
    Enum for complexity levels.
    """
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class ComplexityScore(BaseModel):
    """
    Model for complexity scores.
    """
    overall_score: float = Field(ge=0.0, le=10.0)
    dimension_scores: Dict[ComplexityDimension, float] = Field(default_factory=dict)
    level: ComplexityLevel
    reasoning: str
    token_count: int
    
    @classmethod
    def from_dimension_scores(
        cls,
        dimension_scores: Dict[ComplexityDimension, float],
        token_count: int,
        reasoning: str = ""
    ) -> "ComplexityScore":
        """
        Create a ComplexityScore from dimension scores.
        
        Args:
            dimension_scores: Scores for each complexity dimension
            token_count: Token count of the request
            reasoning: Reasoning for the complexity score
            
        Returns:
            ComplexityScore: Complexity score
        """
        # Calculate overall score (weighted average)
        weights = {
            ComplexityDimension.TOKEN_COUNT: 0.15,
            ComplexityDimension.REASONING_DEPTH: 0.3,
            ComplexityDimension.SPECIALIZED_KNOWLEDGE: 0.25,
            ComplexityDimension.CONTEXT_DEPENDENCY: 0.15,
            ComplexityDimension.OUTPUT_STRUCTURE: 0.15
        }
        
        overall_score = 0.0
        for dimension, score in dimension_scores.items():
            overall_score += score * weights.get(dimension, 0.2)
            
        # Determine complexity level
        level = ComplexityLevel.SIMPLE
        if overall_score >= 7.0:
            level = ComplexityLevel.COMPLEX
        elif overall_score >= 4.0:
            level = ComplexityLevel.MEDIUM
            
        return cls(
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            level=level,
            reasoning=reasoning,
            token_count=token_count
        )
