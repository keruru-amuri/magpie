"""
Unit tests for complexity analysis module.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.model_selection.complexity import ComplexityAnalyzer
from app.models.complexity import ComplexityDimension, ComplexityLevel, ComplexityScore


class TestComplexityAnalyzer:
    """
    Tests for ComplexityAnalyzer.
    """

    def test_rule_based_analysis(self):
        """
        Test rule-based complexity analysis.
        """
        # Create analyzer
        analyzer = ComplexityAnalyzer()

        # Test simple query
        simple_query = "What is the maintenance schedule for a Boeing 737?"
        simple_scores = analyzer._rule_based_analysis(simple_query, 50)

        assert ComplexityDimension.TOKEN_COUNT in simple_scores
        assert simple_scores[ComplexityDimension.TOKEN_COUNT] <= 1.0  # 50 tokens / 100 = 0.5

        # Test complex query with reasoning indicators
        complex_query = "Why does the landing gear system on the Boeing 737 require more frequent maintenance compared to the Airbus A320? Explain the technical differences and analyze the impact on maintenance schedules."
        complex_scores = analyzer._rule_based_analysis(complex_query, 150)

        assert ComplexityDimension.REASONING_DEPTH in complex_scores
        assert complex_scores[ComplexityDimension.REASONING_DEPTH] > simple_scores.get(ComplexityDimension.REASONING_DEPTH, 0)
        assert complex_scores[ComplexityDimension.TOKEN_COUNT] > simple_scores[ComplexityDimension.TOKEN_COUNT]

        # Test query with specialized knowledge indicators
        specialized_query = "What are the technical specifications for the maintenance of the hydraulic system on a Boeing 737 MAX according to the latest regulations?"
        specialized_scores = analyzer._rule_based_analysis(specialized_query, 100)

        assert ComplexityDimension.SPECIALIZED_KNOWLEDGE in specialized_scores
        assert specialized_scores[ComplexityDimension.SPECIALIZED_KNOWLEDGE] > simple_scores.get(ComplexityDimension.SPECIALIZED_KNOWLEDGE, 0)

    @pytest.mark.asyncio
    async def test_analyze_complexity_rule_based_only(self):
        """
        Test analyze_complexity with rule-based analysis only.
        """
        # Create analyzer without LLM service
        analyzer = ComplexityAnalyzer(llm_service=None)

        # Test simple query
        simple_query = "What is the maintenance schedule for a Boeing 737?"
        simple_result = await analyzer.analyze_complexity(simple_query)

        assert isinstance(simple_result, ComplexityScore)
        assert simple_result.level in [ComplexityLevel.SIMPLE, ComplexityLevel.MEDIUM]
        assert "rule-based" in simple_result.reasoning.lower()

        # Test complex query
        complex_query = "Why does the landing gear system on the Boeing 737 require more frequent maintenance compared to the Airbus A320? Explain the technical differences and analyze the impact on maintenance schedules."
        complex_result = await analyzer.analyze_complexity(complex_query)

        assert isinstance(complex_result, ComplexityScore)
        assert complex_result.overall_score > simple_result.overall_score

    @pytest.mark.asyncio
    async def test_analyze_complexity_with_llm(self):
        """
        Test analyze_complexity with LLM-based analysis.
        """
        # Create mock LLM service
        mock_llm_service = AsyncMock()
        mock_llm_service.generate_response_async.return_value = {
            "content": (
                "reasoning_depth: 7.5\n"
                "specialized_knowledge: 8.0\n"
                "context_dependency: 3.0\n"
                "output_structure: 5.0\n"
                "reasoning: This query requires deep technical knowledge and comparative analysis."
            )
        }

        # Create analyzer with mock LLM service
        analyzer = ComplexityAnalyzer(llm_service=mock_llm_service)

        # Test complex query
        complex_query = "Why does the landing gear system on the Boeing 737 require more frequent maintenance compared to the Airbus A320?"
        complex_result = await analyzer.analyze_complexity(complex_query)

        # Verify LLM service was called
        mock_llm_service.generate_response_async.assert_called_once()

        # Verify result
        assert isinstance(complex_result, ComplexityScore)
        assert complex_result.dimension_scores[ComplexityDimension.REASONING_DEPTH] > 5.0
        assert complex_result.dimension_scores[ComplexityDimension.SPECIALIZED_KNOWLEDGE] > 5.0
        assert "technical knowledge" in complex_result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_llm_based_analysis(self):
        """
        Test _llm_based_analysis method.
        """
        # Create mock LLM service
        mock_llm_service = AsyncMock()
        mock_llm_service.generate_response_async.return_value = {
            "content": (
                "token_count: 120\n"
                "reasoning_depth: 7.5\n"
                "specialized_knowledge: 8.0\n"
                "context_dependency: 3.0\n"
                "output_structure: 5.0\n"
                "reasoning: This query requires deep technical knowledge and comparative analysis."
            )
        }

        # Create analyzer with mock LLM service
        analyzer = ComplexityAnalyzer(llm_service=mock_llm_service)

        # Test complex query
        complex_query = "Why does the landing gear system on the Boeing 737 require more frequent maintenance compared to the Airbus A320?"
        dimension_scores, reasoning = await analyzer._llm_based_analysis(complex_query)

        # Verify LLM service was called
        mock_llm_service.generate_response_async.assert_called_once()

        # Verify result
        assert isinstance(dimension_scores, dict)
        assert dimension_scores[ComplexityDimension.REASONING_DEPTH] == 7.5
        assert dimension_scores[ComplexityDimension.SPECIALIZED_KNOWLEDGE] == 8.0
        assert dimension_scores[ComplexityDimension.CONTEXT_DEPENDENCY] == 3.0
        assert dimension_scores[ComplexityDimension.OUTPUT_STRUCTURE] == 5.0
        assert "technical knowledge" in reasoning.lower()

    @pytest.mark.asyncio
    async def test_llm_based_analysis_error_handling(self):
        """
        Test error handling in _llm_based_analysis method.
        """
        # Create mock LLM service that raises an exception
        mock_llm_service = AsyncMock()
        mock_llm_service.generate_response_async.side_effect = Exception("Test error")

        # Create analyzer with mock LLM service
        analyzer = ComplexityAnalyzer(llm_service=mock_llm_service)

        # Test query
        query = "What is the maintenance schedule for a Boeing 737?"

        # Verify that analyze_complexity doesn't raise an exception
        result = await analyzer.analyze_complexity(query)

        # Verify result is based on rule-based analysis
        assert isinstance(result, ComplexityScore)
        assert "rule-based" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_llm_based_analysis_parsing_error(self):
        """
        Test parsing error handling in _llm_based_analysis method.
        """
        # Create mock LLM service with invalid response format
        mock_llm_service = AsyncMock()
        mock_llm_service.generate_response_async.return_value = {
            "content": "This is not a valid format for complexity analysis."
        }

        # Create analyzer with mock LLM service
        analyzer = ComplexityAnalyzer(llm_service=mock_llm_service)

        # Test query
        query = "What is the maintenance schedule for a Boeing 737?"

        # Call _llm_based_analysis directly
        dimension_scores, reasoning = await analyzer._llm_based_analysis(query)

        # Print for debugging
        print(f"Dimension scores: {dimension_scores}")
        print(f"Reasoning: '{reasoning}'")

        # Verify empty results are returned
        assert dimension_scores == {}
