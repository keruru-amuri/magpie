"""
Unit tests for the response formatter.
"""
import pytest
from unittest.mock import MagicMock

from app.core.orchestrator.formatter import ResponseFormatter
from app.models.conversation import AgentType
from app.models.orchestrator import OrchestratorResponse, RoutingResult, RequestClassification


@pytest.fixture
def formatter():
    """
    Create a response formatter.
    """
    return ResponseFormatter()


class TestResponseFormatter:
    """
    Tests for the ResponseFormatter class.
    """

    def test_format_response_basic(self, formatter):
        """
        Test formatting a basic response.
        """
        # Test response content
        response_content = "This is a test response."

        # Format response
        result = formatter.format_response(
            response_content=response_content,
            agent_type=AgentType.DOCUMENTATION,
            agent_name="Documentation Assistant",
            confidence=0.9,
            conversation_id="test-conversation-id"
        )

        # Verify result
        assert isinstance(result, OrchestratorResponse)
        assert result.response == response_content
        assert result.agent_type == AgentType.DOCUMENTATION
        assert result.agent_name == "Documentation Assistant"
        assert result.confidence == 0.9
        assert result.conversation_id == "test-conversation-id"
        assert result.metadata is None
        assert result.followup_questions is None

    def test_format_response_with_metadata(self, formatter):
        """
        Test formatting a response with metadata.
        """
        # Test response content and metadata
        response_content = "This is a test response."
        metadata = {"key1": "value1", "key2": "value2"}

        # Format response
        result = formatter.format_response(
            response_content=response_content,
            agent_type=AgentType.TROUBLESHOOTING,
            agent_name="Troubleshooting Advisor",
            confidence=0.8,
            conversation_id="test-conversation-id",
            metadata=metadata
        )

        # Verify result
        assert isinstance(result, OrchestratorResponse)
        assert result.response == response_content
        assert result.agent_type == AgentType.TROUBLESHOOTING
        assert result.agent_name == "Troubleshooting Advisor"
        assert result.confidence == 0.8
        assert result.conversation_id == "test-conversation-id"
        assert result.metadata == metadata
        assert result.followup_questions is None

    def test_format_response_with_source_references(self, formatter):
        """
        Test formatting a response with source references.
        """
        # Test response content and source references
        response_content = "This is a test response."
        source_references = [
            {"title": "Maintenance Manual", "document_id": "MM-123"},
            {"title": "Technical Bulletin", "url": "https://example.com/tb-456"}
        ]

        # Format response
        result = formatter.format_response(
            response_content=response_content,
            agent_type=AgentType.DOCUMENTATION,
            agent_name="Documentation Assistant",
            confidence=0.9,
            conversation_id="test-conversation-id",
            source_references=source_references
        )

        # Verify result
        assert isinstance(result, OrchestratorResponse)
        assert "This is a test response." in result.response
        assert "Sources:" in result.response
        assert "Maintenance Manual" in result.response
        assert "MM-123" in result.response
        assert "Technical Bulletin" in result.response
        assert "https://example.com/tb-456" in result.response

    def test_format_response_with_followup_questions_section(self, formatter):
        """
        Test formatting a response with a followup questions section.
        """
        # Test response content with followup questions section
        response_content = (
            "This is a test response.\n\n"
            "Follow-up Questions:\n"
            "- What is the next step?\n"
            "- Do you need more information?\n"
            "- Would you like to see an example?"
        )

        # Format response
        result = formatter.format_response(
            response_content=response_content,
            agent_type=AgentType.MAINTENANCE,
            agent_name="Maintenance Procedure Generator",
            confidence=0.7,
            conversation_id="test-conversation-id"
        )

        # Verify result
        assert isinstance(result, OrchestratorResponse)
        assert result.response == response_content
        assert result.agent_type == AgentType.MAINTENANCE
        assert result.agent_name == "Maintenance Procedure Generator"
        assert result.confidence == 0.7
        assert result.conversation_id == "test-conversation-id"
        assert result.metadata is None
        assert result.followup_questions is not None
        assert len(result.followup_questions) == 3
        assert "What is the next step?" in result.followup_questions
        assert "Do you need more information?" in result.followup_questions
        assert "Would you like to see an example?" in result.followup_questions

    def test_format_multi_agent_response(self, formatter):
        """
        Test formatting responses from multiple agents.
        """
        # Create primary response
        primary_response = OrchestratorResponse(
            response="This is the primary response from the documentation agent.",
            agent_type=AgentType.DOCUMENTATION,
            agent_name="Documentation Assistant",
            confidence=0.9,
            conversation_id="test-conversation-id",
            followup_questions=["Would you like more information?"]
        )

        # Create secondary responses
        secondary_responses = [
            OrchestratorResponse(
                response="This is additional information from the troubleshooting agent.",
                agent_type=AgentType.TROUBLESHOOTING,
                agent_name="Troubleshooting Advisor",
                confidence=0.8,
                conversation_id="test-conversation-id",
                followup_questions=["Have you checked the hydraulic system?"]
            ),
            OrchestratorResponse(
                response="This is maintenance procedure information.",
                agent_type=AgentType.MAINTENANCE,
                agent_name="Maintenance Procedure Generator",
                confidence=0.7,
                conversation_id="test-conversation-id",
                followup_questions=["Do you need the full procedure?"]
            )
        ]

        # Create routing result with a real classification
        classification = RequestClassification(
            agent_type=AgentType.DOCUMENTATION,
            confidence=0.9,
            reasoning="This is a documentation request"
        )

        routing_result = RoutingResult(
            agent_type=AgentType.DOCUMENTATION,
            agent_config_id=1,
            classification=classification,
            requires_multiple_agents=True,
            additional_agent_types=[AgentType.TROUBLESHOOTING, AgentType.MAINTENANCE]
        )

        # Format multi-agent response
        result = formatter.format_multi_agent_response(
            primary_response=primary_response,
            secondary_responses=secondary_responses,
            routing_result=routing_result
        )

        # Verify result
        assert isinstance(result, OrchestratorResponse)
        assert primary_response.response in result.response
        assert "Additional information:" in result.response
        assert "From Troubleshooting Advisor" in result.response
        assert "From Maintenance Procedure Generator" in result.response

        # Verify followup questions are combined
        assert result.followup_questions is not None
        assert len(result.followup_questions) == 3
        assert any("Would you like more information?" in q for q in result.followup_questions)
        assert any("[troubleshooting]" in q.lower() for q in result.followup_questions)
        assert any("[maintenance]" in q.lower() for q in result.followup_questions)

    def test_create_inter_agent_prompt(self, formatter):
        """
        Test creating a prompt for inter-agent communication.
        """
        # Test parameters
        query = "How do I troubleshoot low hydraulic pressure?"
        primary_agent_type = AgentType.DOCUMENTATION
        secondary_agent_type = AgentType.TROUBLESHOOTING
        primary_response = "According to the documentation, low hydraulic pressure can be caused by several factors."

        # Create inter-agent prompt
        prompt = formatter.create_inter_agent_prompt(
            query=query,
            primary_agent_type=primary_agent_type,
            secondary_agent_type=secondary_agent_type,
            primary_response=primary_response
        )

        # Verify prompt
        assert "You are a specialized troubleshooting agent" in prompt
        assert "The primary agent handling this query is a documentation agent" in prompt
        assert query in prompt
        assert primary_response in prompt
        assert "Please provide additional information" in prompt

        # Test without primary response
        prompt_no_response = formatter.create_inter_agent_prompt(
            query=query,
            primary_agent_type=primary_agent_type,
            secondary_agent_type=secondary_agent_type
        )

        # Verify prompt
        assert "You are a specialized troubleshooting agent" in prompt_no_response
        assert "The primary agent handling this query is a documentation agent" in prompt_no_response
        assert query in prompt_no_response
        assert "Please provide information from your troubleshooting perspective" in prompt_no_response

    def test_clean_response(self, formatter):
        """
        Test cleaning a response.
        """
        # Test response content with system instructions
        response_content = (
            "As an AI assistant, I'll help you with your question.\n\n"
            "```json\n{\"key\": \"value\"}\n```\n\n"
            "This is the actual response content.\n\n"
            "```\nSome code block\n```"
        )

        # Clean response
        cleaned = formatter._clean_response(response_content)

        # Verify result
        assert "As an AI assistant" not in cleaned
        assert "```json" not in cleaned
        assert "{\"key\": \"value\"}" not in cleaned
        assert "This is the actual response content" in cleaned

    def test_truncate_response(self, formatter):
        """
        Test truncating a response.
        """
        # Test long response
        long_response = "This is a very long response. " * 20 + "It ends with a period."

        # Truncate response
        truncated = formatter._truncate_response(long_response, max_length=50)

        # Verify result
        assert len(truncated) < len(long_response)
        assert truncated.endswith("[...]")
        assert "." in truncated  # Should end at a sentence boundary

        # Test short response (should not be truncated)
        short_response = "This is a short response."
        truncated_short = formatter._truncate_response(short_response, max_length=50)
        assert truncated_short == short_response

    def test_add_confidence_indicator(self, formatter):
        """
        Test adding a confidence indicator to a response.
        """
        # Test response
        response = "The hydraulic system requires maintenance."

        # Add confidence indicator with high confidence
        high_confidence = formatter.add_confidence_indicator(
            response=response,
            confidence=0.9,
            agent_type=AgentType.MAINTENANCE
        )

        # Verify result contains a high confidence phrase
        high_confidence_phrases = formatter._confidence_phrases["high"]
        assert any(phrase in high_confidence for phrase in high_confidence_phrases)

        # Add confidence indicator with medium confidence
        medium_confidence = formatter.add_confidence_indicator(
            response=response,
            confidence=0.6,
            agent_type=AgentType.MAINTENANCE
        )

        # Verify result contains a medium confidence phrase
        medium_confidence_phrases = formatter._confidence_phrases["medium"]
        assert any(phrase in medium_confidence for phrase in medium_confidence_phrases)

        # Add confidence indicator with low confidence
        low_confidence = formatter.add_confidence_indicator(
            response=response,
            confidence=0.3,
            agent_type=AgentType.MAINTENANCE
        )

        # Verify result contains a low confidence phrase
        low_confidence_phrases = formatter._confidence_phrases["low"]
        assert any(phrase in low_confidence for phrase in low_confidence_phrases)

    def test_format_response_with_template(self, formatter):
        """
        Test formatting a response with a template.
        """
        # Test response
        response = "The hydraulic system requires maintenance."

        # Format response for documentation agent
        doc_response = formatter.format_response_with_template(
            response=response,
            agent_type=AgentType.DOCUMENTATION,
            confidence=0.9
        )

        # Verify result
        assert "Based on the technical documentation" in doc_response

        # Format response for troubleshooting agent
        ts_response = formatter.format_response_with_template(
            response=response,
            agent_type=AgentType.TROUBLESHOOTING,
            confidence=0.9
        )

        # Verify result
        assert "Based on troubleshooting analysis" in ts_response

        # Format response for maintenance agent
        maint_response = formatter.format_response_with_template(
            response=response,
            agent_type=AgentType.MAINTENANCE,
            confidence=0.9
        )

        # Verify result
        assert "For maintenance procedures" in maint_response

    def test_format_response_error_handling(self, formatter):
        """
        Test error handling during response formatting.
        """
        # Mock _clean_response to raise an exception
        formatter._clean_response = MagicMock(side_effect=Exception("Test error"))

        # Format response (should not raise an exception)
        result = formatter.format_response(
            response_content="This is a test response.",
            agent_type=AgentType.DOCUMENTATION,
            agent_name="Documentation Assistant",
            confidence=0.9,
            conversation_id="test-conversation-id"
        )

        # Verify result contains an error message
        assert isinstance(result, OrchestratorResponse)
        assert "error" in result.response.lower() or "apologize" in result.response.lower()
        assert result.confidence == 0.0
        assert result.metadata is not None
        assert "error" in result.metadata
