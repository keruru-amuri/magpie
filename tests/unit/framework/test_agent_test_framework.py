"""
Tests for the agent testing framework.

This module demonstrates the usage of the agent testing framework.
"""
import pytest

from app.models.conversation import AgentType
from app.models.agent import ModelSize

from tests.framework.generators.agent_test_case_generator import AgentTestCaseGenerator, QueryComplexity
from tests.framework.assertions.response_assertions import ResponseAssertions

# Import fixtures
pytest_plugins = ["tests.framework.fixtures.agent_fixtures"]


class TestAgentTestFramework:
    """
    Tests for the agent testing framework.
    """

    def test_test_case_generator(self):
        """
        Test the test case generator.
        """
        # Create generator
        generator = AgentTestCaseGenerator(seed=42)

        # Generate test case
        test_case = generator.generate_test_case(
            agent_type=AgentType.DOCUMENTATION,
            complexity=QueryComplexity.MODERATE,
            include_conversation_history=True,
            include_context=True
        )

        # Verify test case
        assert test_case["agent_type"] == AgentType.DOCUMENTATION
        assert test_case["complexity"] == QueryComplexity.MODERATE
        assert "query" in test_case
        assert "expected_response_patterns" in test_case
        assert "conversation_history" in test_case
        assert "context" in test_case

        # Generate multiple test cases
        test_cases = generator.generate_test_cases(
            count=5,
            agent_types=[AgentType.DOCUMENTATION, AgentType.TROUBLESHOOTING],
            complexities=[QueryComplexity.SIMPLE, QueryComplexity.MODERATE]
        )

        # Verify test cases
        assert len(test_cases) == 5
        for case in test_cases:
            assert case["agent_type"] in [AgentType.DOCUMENTATION, AgentType.TROUBLESHOOTING]
            assert case["complexity"] in [QueryComplexity.SIMPLE, QueryComplexity.MODERATE]
            assert "query" in case
            assert "expected_response_patterns" in case

    def test_response_assertions(self):
        """
        Test the response assertions.
        """
        # Sample response
        response = """
        The recommended tire pressure for a Boeing 737-800 is 200 psi for the main landing gear
        and 180 psi for the nose landing gear. These values may vary slightly based on the specific
        aircraft configuration and operating conditions.

        Always refer to the Aircraft Maintenance Manual (AMM) for the exact specifications for your
        aircraft. The tire pressure should be checked daily as part of the pre-flight inspection.
        """

        # Test assertions
        assert ResponseAssertions.assert_response_contains(
            response, "recommended tire pressure"
        )

        assert ResponseAssertions.assert_response_matches_pattern(
            response, r"\d+ psi"
        )

        assert ResponseAssertions.assert_response_relevance(
            response, "What is the tire pressure for Boeing 737?"
        )

        # Test with expected patterns that are actually in the response
        quality = ResponseAssertions.assert_response_quality(
            response,
            "What is the tire pressure for Boeing 737?",
            ["tire pressure", "landing gear", "maintenance manual"]
        )

        # Assert quality passes threshold
        assert quality["passes_threshold"]
        assert quality["relevance"]
        assert len(quality["pattern_matches"]) >= 2

    def test_input_simulator_basic(self, input_simulator):
        """
        Test the basic functionality of the input simulator.

        Args:
            input_simulator: Input simulator fixture
        """
        # Generate random query
        query = input_simulator.generate_random_query(AgentType.DOCUMENTATION)
        assert isinstance(query, str)
        assert len(query) > 0

        # Generate agent context
        context = input_simulator.generate_agent_context(AgentType.MAINTENANCE)
        assert "aircraft_type" in context
        assert "system" in context
        assert "maintenance_type" in context

        # Generate conversation history
        history = input_simulator.generate_conversation_history(
            agent_type=AgentType.DOCUMENTATION,
            num_turns=2
        )
        assert len(history) == 5  # system + 2 turns (user + assistant)
        assert history[0]["role"] == "system"
        assert history[1]["role"] == "user"
        assert history[2]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_mock_llm_service(self, mock_llm_service):
        """
        Test the mock LLM service.

        Args:
            mock_llm_service: Mock LLM service fixture
        """
        # Generate response
        response = await mock_llm_service.generate_response_async(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the tire pressure for Boeing 737?"}
            ],
            model_size=ModelSize.MEDIUM,
            temperature=0.7,
            max_tokens=1000
        )

        # Verify response
        assert "content" in response
        assert "model" in response
        assert "usage" in response
        assert "What is the tire pressure for Boeing 737?" in response["content"]

        # Verify call history
        assert len(mock_llm_service.call_history) == 1
        assert mock_llm_service.call_history[0]["model_size"] == ModelSize.MEDIUM

        # Test complexity analysis
        complexity = await mock_llm_service.analyze_complexity_async(
            query="What is the recommended tire pressure for a Boeing 737-800 aircraft?"
        )

        assert "complexity" in complexity
        assert "score" in complexity
        assert "dimensions" in complexity
        assert "reasoning" in complexity


