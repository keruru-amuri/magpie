"""
Unit tests for the request classifier.
"""
import pytest
from unittest.mock import AsyncMock

from app.core.orchestrator.classifier import ContentType, RequestClassifier
from app.models.conversation import AgentType
from app.models.orchestrator import AgentCapability, AgentMetadata, RequestClassification


@pytest.fixture
def mock_llm_service():
    """
    Create a mock LLM service.
    """
    mock_service = AsyncMock()
    mock_service.generate_custom_response_async = AsyncMock()
    return mock_service


@pytest.fixture
def classifier(mock_llm_service):
    """
    Create a request classifier with a mock LLM service.
    """
    return RequestClassifier(mock_llm_service, cache_size=10)


@pytest.fixture
def available_agents():
    """
    Create a list of available agent metadata.
    """
    return [
        AgentMetadata(
            agent_type=AgentType.DOCUMENTATION,
            name="Documentation Assistant",
            description="Helps find information in technical documentation",
            capabilities=[
                AgentCapability(
                    name="Documentation Search",
                    description="Find and extract information from technical documentation",
                    keywords=["manual", "document", "find", "search", "information"],
                    examples=["Where can I find information about landing gear maintenance?"]
                )
            ],
            config_id=1,
            is_default=True
        ),
        AgentMetadata(
            agent_type=AgentType.TROUBLESHOOTING,
            name="Troubleshooting Advisor",
            description="Helps diagnose and resolve issues",
            capabilities=[
                AgentCapability(
                    name="Problem Diagnosis",
                    description="Diagnose issues based on symptoms",
                    keywords=["problem", "issue", "error", "diagnose", "troubleshoot"],
                    examples=["The hydraulic system is showing low pressure, what could be the cause?"]
                )
            ],
            config_id=2,
            is_default=True
        ),
        AgentMetadata(
            agent_type=AgentType.MAINTENANCE,
            name="Maintenance Procedure Generator",
            description="Creates maintenance procedures",
            capabilities=[
                AgentCapability(
                    name="Procedure Generation",
                    description="Create maintenance procedures",
                    keywords=["procedure", "steps", "maintenance", "how to"],
                    examples=["What are the steps to replace the fuel filter?"]
                )
            ],
            config_id=3,
            is_default=True
        )
    ]


class TestRequestClassifier:
    """
    Tests for the RequestClassifier class.
    """

    @pytest.mark.asyncio
    async def test_classify_request_documentation(self, classifier, mock_llm_service, available_agents):
        """
        Test classifying a documentation request.
        """
        # Mock LLM response
        mock_llm_service.generate_custom_response_async.return_value = {
            "content": '{"agent_type": "documentation", "confidence": 0.9, "reasoning": "This is a request for documentation"}'
        }

        # Test query
        query = "Where can I find information about landing gear maintenance?"

        # Classify request
        result = await classifier.classify_request(query, available_agents)

        # Verify result
        assert isinstance(result, RequestClassification)
        assert result.agent_type == AgentType.DOCUMENTATION
        assert result.confidence == 0.9
        assert "documentation" in result.reasoning.lower()

        # Verify LLM service was called correctly
        mock_llm_service.generate_custom_response_async.assert_called_once()
        call_args = mock_llm_service.generate_custom_response_async.call_args[1]
        assert call_args["model_size"] == "small"
        assert call_args["temperature"] == 0.3
        assert len(call_args["messages"]) == 2  # System prompt + user query

    @pytest.mark.asyncio
    async def test_classify_request_with_cache(self, classifier, mock_llm_service, available_agents):
        """
        Test that classification results are cached.
        """
        # Mock LLM response
        mock_llm_service.generate_custom_response_async.return_value = {
            "content": '{"agent_type": "documentation", "confidence": 0.9, "reasoning": "This is a request for documentation"}'
        }

        # Test query
        query = "Where can I find information about landing gear maintenance?"

        # Classify request first time
        result1 = await classifier.classify_request(query, available_agents)

        # Reset mock to verify it's not called again
        mock_llm_service.generate_custom_response_async.reset_mock()

        # Classify same request again
        result2 = await classifier.classify_request(query, available_agents)

        # Verify results are the same
        assert result1.agent_type == result2.agent_type
        assert result1.confidence == result2.confidence

        # Verify LLM service was not called the second time
        mock_llm_service.generate_custom_response_async.assert_not_called()

    def test_quick_classify(self, classifier):
        """
        Test quick classification based on keywords.
        """
        # Documentation query
        doc_query = "Where can I find the manual for landing gear maintenance?"
        agent_type, confidence = classifier._quick_classify(doc_query)
        assert agent_type == AgentType.DOCUMENTATION
        assert confidence >= 0.5

        # Troubleshooting query
        ts_query = "I have a problem with the hydraulic system, it's not working properly."
        agent_type, confidence = classifier._quick_classify(ts_query)
        assert agent_type == AgentType.TROUBLESHOOTING
        assert confidence >= 0.5

        # Maintenance query
        maint_query = "What are the steps to replace the fuel filter?"
        agent_type, confidence = classifier._quick_classify(maint_query)
        assert agent_type == AgentType.MAINTENANCE
        assert confidence >= 0.5

        # Ambiguous query
        ambig_query = "Hello, I need some help."
        agent_type, confidence = classifier._quick_classify(ambig_query)
        assert agent_type is None
        assert confidence == 0.0

    def test_detect_content_type(self, classifier):
        """
        Test content type detection.
        """
        # Text content
        text_query = "Where can I find information about landing gear maintenance?"
        assert classifier._detect_content_type(text_query) == ContentType.TEXT

        # Code content
        code_query = "```python\ndef test_function():\n    print('Hello world')\n```"
        assert classifier._detect_content_type(code_query) == ContentType.CODE

        # HTML code
        html_query = "Can you help me with this code: <code>const x = 10;</code>"
        assert classifier._detect_content_type(html_query) == ContentType.CODE

        # Programming keywords
        prog_query = "I have an issue with this function: getData() { return fetch('/api/data'); }"
        assert classifier._detect_content_type(prog_query) == ContentType.CODE

        # Structured data
        json_query = "I have this data: { \"name\": \"John\", \"age\": 30 }"
        assert classifier._detect_content_type(json_query) == ContentType.STRUCTURED_DATA

        # Array data
        array_query = "Here's a list: [1, 2, 3, 4, 5]"
        assert classifier._detect_content_type(array_query) == ContentType.STRUCTURED_DATA

    @pytest.mark.asyncio
    async def test_classify_request_troubleshooting(self, classifier, mock_llm_service, available_agents):
        """
        Test classifying a troubleshooting request.
        """
        # Mock LLM response
        mock_llm_service.generate_custom_response_async.return_value = {
            "content": '{"agent_type": "troubleshooting", "confidence": 0.8, "reasoning": "This is a troubleshooting request"}'
        }

        # Test query
        query = "The hydraulic system is showing low pressure, what could be the cause?"

        # Classify request
        result = await classifier.classify_request(query, available_agents)

        # Verify result
        assert isinstance(result, RequestClassification)
        assert result.agent_type == AgentType.TROUBLESHOOTING
        assert result.confidence == 0.8
        assert "troubleshooting" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_classify_request_maintenance(self, classifier, mock_llm_service, available_agents):
        """
        Test classifying a maintenance request.
        """
        # Mock LLM response
        mock_llm_service.generate_custom_response_async.return_value = {
            "content": '{"agent_type": "maintenance", "confidence": 0.7, "reasoning": "This is a maintenance request"}'
        }

        # Test query
        query = "What are the steps to replace the fuel filter?"

        # Classify request
        result = await classifier.classify_request(query, available_agents)

        # Verify result
        assert isinstance(result, RequestClassification)
        assert result.agent_type == AgentType.MAINTENANCE
        assert result.confidence == 0.7
        assert "maintenance" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_classify_request_with_conversation_history(self, classifier, mock_llm_service, available_agents):
        """
        Test classifying a request with conversation history.
        """
        # Mock LLM response
        mock_llm_service.generate_custom_response_async.return_value = {
            "content": '{"agent_type": "documentation", "confidence": 0.85, "reasoning": "This is a documentation request"}'
        }

        # Test query and conversation history
        query = "Where can I find that information?"
        conversation_history = [
            {"role": "user", "content": "I need information about landing gear maintenance."},
            {"role": "assistant", "content": "I can help you find information about landing gear maintenance."}
        ]

        # Classify request
        result = await classifier.classify_request(query, available_agents, conversation_history)

        # Verify result
        assert isinstance(result, RequestClassification)
        assert result.agent_type == AgentType.DOCUMENTATION
        assert result.confidence == 0.85

        # Verify LLM service was called with conversation history
        mock_llm_service.generate_custom_response_async.assert_called_once()
        call_args = mock_llm_service.generate_custom_response_async.call_args[1]
        assert len(call_args["messages"]) == 4  # System prompt + 2 history messages + user query

    @pytest.mark.asyncio
    async def test_classify_request_error_handling(self, classifier, mock_llm_service, available_agents):
        """
        Test error handling during classification.
        """
        # Mock LLM service to raise an exception
        mock_llm_service.generate_custom_response_async.side_effect = Exception("Test error")

        # Test query
        query = "Where can I find information about landing gear maintenance?"

        # Classify request (should not raise an exception)
        result = await classifier.classify_request(query, available_agents)

        # Verify result defaults to documentation agent
        assert isinstance(result, RequestClassification)
        assert result.agent_type == AgentType.DOCUMENTATION
        assert result.confidence == 0.3
        assert "failed" in result.reasoning.lower() or "default" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_parse_classification_response_invalid_json(self, classifier, available_agents):
        """
        Test parsing an invalid JSON response.
        """
        # Invalid JSON response
        response_content = "This is not valid JSON"

        # Parse response
        result = classifier._parse_classification_response(response_content, available_agents)

        # Verify result defaults to documentation agent
        assert isinstance(result, RequestClassification)
        assert result.agent_type == AgentType.DOCUMENTATION
        assert result.confidence == 0.3
        assert "failed" in result.reasoning.lower() or "default" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_parse_classification_response_invalid_agent_type(self, classifier, available_agents):
        """
        Test parsing a response with an invalid agent type.
        """
        # Response with invalid agent type
        response_content = '{"agent_type": "invalid", "confidence": 0.9, "reasoning": "This is a test"}'

        # Parse response
        result = classifier._parse_classification_response(response_content, available_agents)

        # Verify result defaults to documentation agent
        assert isinstance(result, RequestClassification)
        assert result.agent_type == AgentType.DOCUMENTATION
        assert result.confidence > 0.0
        assert result.confidence <= 1.0
