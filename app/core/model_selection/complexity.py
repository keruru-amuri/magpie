"""
Complexity analysis module for the MAGPIE platform.

This module provides functionality for analyzing the complexity of user requests
to inform model selection decisions.
"""
import logging
import re
from typing import Dict, List, Optional, Tuple

from app.models.complexity import ComplexityDimension, ComplexityLevel, ComplexityScore
from app.services.llm_service import LLMService, ModelSize
from app.services.token_utils import count_tokens_azure

# Configure logging
logger = logging.getLogger(__name__)


class ComplexityAnalyzer:
    """
    Analyzer for determining request complexity.
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize complexity analyzer.

        Args:
            llm_service: LLM service for advanced complexity analysis
        """
        self.llm_service = llm_service

    async def analyze_complexity(
        self, 
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> ComplexityScore:
        """
        Analyze the complexity of a user query.

        Args:
            query: User query
            conversation_history: Optional conversation history

        Returns:
            ComplexityScore: Complexity score
        """
        # Count tokens
        token_count = count_tokens_azure(query, "gpt-4.1")
        
        # Perform rule-based analysis first
        dimension_scores = self._rule_based_analysis(query, token_count)
        
        # If LLM service is available, enhance with LLM-based analysis
        if self.llm_service:
            try:
                llm_dimension_scores, reasoning = await self._llm_based_analysis(
                    query, conversation_history
                )
                
                # Combine rule-based and LLM-based scores (giving more weight to LLM)
                for dimension, score in llm_dimension_scores.items():
                    if dimension in dimension_scores:
                        # 70% LLM, 30% rule-based
                        dimension_scores[dimension] = (score * 0.7) + (dimension_scores[dimension] * 0.3)
                    else:
                        dimension_scores[dimension] = score
            except Exception as e:
                # Log error but continue with rule-based analysis
                logger.error(f"LLM-based complexity analysis failed: {str(e)}")
                reasoning = "Analysis based on rule-based metrics only."
        else:
            reasoning = "Analysis based on rule-based metrics only."
            
        # Create complexity score
        return ComplexityScore.from_dimension_scores(
            dimension_scores=dimension_scores,
            token_count=token_count,
            reasoning=reasoning
        )

    def _rule_based_analysis(
        self, 
        query: str,
        token_count: int
    ) -> Dict[ComplexityDimension, float]:
        """
        Perform rule-based complexity analysis.

        Args:
            query: User query
            token_count: Token count of the query

        Returns:
            Dict[ComplexityDimension, float]: Scores for each complexity dimension
        """
        dimension_scores = {}
        
        # 1. Token Count
        # Scale: 0-10 based on token count (0-1000 tokens)
        token_score = min(10.0, token_count / 100)
        dimension_scores[ComplexityDimension.TOKEN_COUNT] = token_score
        
        # 2. Reasoning Depth
        # Look for indicators of complex reasoning
        reasoning_indicators = [
            r"why", r"how", r"explain", r"analyze", r"compare", r"difference",
            r"relationship", r"cause", r"effect", r"impact", r"consequence"
        ]
        reasoning_score = 0.0
        for indicator in reasoning_indicators:
            if re.search(rf"\b{indicator}\b", query, re.IGNORECASE):
                reasoning_score += 1.5
        
        # Check for multi-step reasoning
        if re.search(r"step[s]? (by|for)", query, re.IGNORECASE):
            reasoning_score += 2.0
            
        dimension_scores[ComplexityDimension.REASONING_DEPTH] = min(10.0, reasoning_score)
        
        # 3. Specialized Knowledge
        # Look for technical terms and specialized domains
        specialized_indicators = [
            r"technical", r"specific", r"specialized", r"aircraft", r"maintenance",
            r"repair", r"overhaul", r"procedure", r"regulation", r"compliance"
        ]
        specialized_score = 0.0
        for indicator in specialized_indicators:
            if re.search(rf"\b{indicator}\b", query, re.IGNORECASE):
                specialized_score += 1.5
                
        dimension_scores[ComplexityDimension.SPECIALIZED_KNOWLEDGE] = min(10.0, specialized_score)
        
        # 4. Context Dependency
        # Check if the query depends on previous context
        context_indicators = [
            r"previous", r"earlier", r"before", r"last", r"mentioned",
            r"that", r"this", r"it", r"they", r"those"
        ]
        context_score = 0.0
        for indicator in context_indicators:
            if re.search(rf"\b{indicator}\b", query, re.IGNORECASE):
                context_score += 1.5
                
        dimension_scores[ComplexityDimension.CONTEXT_DEPENDENCY] = min(10.0, context_score)
        
        # 5. Output Structure
        # Check for requests requiring structured output
        structure_indicators = [
            r"list", r"table", r"format", r"json", r"structure", r"organize",
            r"categorize", r"classify", r"summarize", r"bullet points"
        ]
        structure_score = 0.0
        for indicator in structure_indicators:
            if re.search(rf"\b{indicator}\b", query, re.IGNORECASE):
                structure_score += 1.5
                
        dimension_scores[ComplexityDimension.OUTPUT_STRUCTURE] = min(10.0, structure_score)
        
        return dimension_scores

    async def _llm_based_analysis(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[Dict[ComplexityDimension, float], str]:
        """
        Perform LLM-based complexity analysis.

        Args:
            query: User query
            conversation_history: Optional conversation history

        Returns:
            Tuple[Dict[ComplexityDimension, float], str]: Scores for each complexity dimension and reasoning

        Raises:
            Exception: If LLM analysis fails
        """
        # Use a smaller model for complexity analysis to save costs
        response = await self.llm_service.generate_response_async(
            template_name="complexity_analysis",
            variables={
                "query": query,
                "conversation_history": conversation_history or []
            },
            model_size=ModelSize.SMALL
        )
        
        try:
            # Parse the response
            content = response.get("content", "")
            
            # Extract scores and reasoning
            dimension_scores = {}
            reasoning = ""
            
            # Parse scores (expected format: "DIMENSION: SCORE")
            for dimension in ComplexityDimension:
                pattern = rf"{dimension.value}:\s*(\d+(\.\d+)?)"
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    score = float(match.group(1))
                    dimension_scores[dimension] = min(10.0, score)
            
            # Extract reasoning
            reasoning_match = re.search(r"reasoning:(.*?)(\n|$)", content, re.IGNORECASE | re.DOTALL)
            if reasoning_match:
                reasoning = reasoning_match.group(1).strip()
            
            return dimension_scores, reasoning
        except Exception as e:
            logger.error(f"Failed to parse LLM complexity analysis: {str(e)}")
            # Return empty results, will fall back to rule-based analysis
            return {}, "LLM analysis parsing failed."
