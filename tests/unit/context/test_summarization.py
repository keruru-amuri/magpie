"""
Unit tests for context summarization.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.core.context.summarization import ConversationSummarizer, SummaryManager
from app.models.conversation import Message, MessageRole
from app.services.llm_service import LLMService


class TestConversationSummarizer:
    """
    Test conversation summarizer.
    """
    
    @pytest.fixture
    def mock_llm_service(self):
        """
        Create a mock LLM service.
        """
        service = MagicMock(spec=LLMService)
        service.generate_completion = AsyncMock(return_value={"content": "This is a summary"})
        return service
    
    @pytest.fixture
    def summarizer(self, mock_llm_service):
        """
        Create a conversation summarizer.
        """
        return ConversationSummarizer(mock_llm_service)
    
    @pytest.fixture
    def mock_messages(self):
        """
        Create mock messages.
        """
        return [
            MagicMock(
                spec=Message,
                id=1,
                role=MessageRole.USER,
                content="Hello, I need help with the hydraulic system on a Boeing 737."
            ),
            MagicMock(
                spec=Message,
                id=2,
                role=MessageRole.ASSISTANT,
                content="I'd be happy to help with the hydraulic system. What specific issue are you experiencing?"
            ),
            MagicMock(
                spec=Message,
                id=3,
                role=MessageRole.USER,
                content="The pressure is dropping during operation and I'm not sure what's causing it."
            ),
            MagicMock(
                spec=Message,
                id=4,
                role=MessageRole.ASSISTANT,
                content="Pressure drops in the hydraulic system can be caused by several issues. Let me help you troubleshoot."
            )
        ]
    
    @pytest.mark.asyncio
    async def test_summarize_messages(self, summarizer, mock_messages, mock_llm_service):
        """
        Test summarizing messages.
        """
        # Call summarize_messages
        summary = await summarizer.summarize_messages(mock_messages)
        
        # Verify result
        assert summary == "This is a summary"
        
        # Verify LLM service was called
        mock_llm_service.generate_completion.assert_called_once()
    
    def test_format_messages_for_summarization(self, summarizer, mock_messages):
        """
        Test formatting messages for summarization.
        """
        # Call _format_messages_for_summarization
        formatted = summarizer._format_messages_for_summarization(mock_messages)
        
        # Verify result
        assert len(formatted) == 4
        assert formatted[0].startswith("User: ")
        assert formatted[1].startswith("Assistant: ")
        assert formatted[2].startswith("User: ")
        assert formatted[3].startswith("Assistant: ")
    
    def test_should_summarize(self, summarizer, mock_messages):
        """
        Test should_summarize.
        """
        # Test with few messages (below threshold)
        result = summarizer.should_summarize(
            mock_messages,
            token_threshold=10000,
            message_count_threshold=10
        )
        assert result is False
        
        # Test with many messages (above threshold)
        result = summarizer.should_summarize(
            mock_messages,
            token_threshold=10000,
            message_count_threshold=3
        )
        assert result is True
        
        # Test with high token count (above threshold)
        with patch('app.core.context.summarization.count_tokens_azure', return_value=1000):
            result = summarizer.should_summarize(
                mock_messages,
                token_threshold=3000,
                message_count_threshold=10
            )
            assert result is True
    
    def test_identify_segments_for_summarization(self, summarizer, mock_messages):
        """
        Test identifying segments for summarization.
        """
        # Test with segment size larger than message count
        segments = summarizer.identify_segments_for_summarization(
            mock_messages,
            segment_size=10,
            overlap=2
        )
        assert segments == []
        
        # Test with segment size smaller than message count
        segments = summarizer.identify_segments_for_summarization(
            mock_messages,
            segment_size=2,
            overlap=1
        )
        assert len(segments) == 3
        assert segments[0]["start_idx"] == 0
        assert segments[0]["end_idx"] == 1
        assert segments[1]["start_idx"] == 1
        assert segments[1]["end_idx"] == 2
        assert segments[2]["start_idx"] == 2
        assert segments[2]["end_idx"] == 3


class TestSummaryManager:
    """
    Test summary manager.
    """
    
    @pytest.fixture
    def mock_llm_service(self):
        """
        Create a mock LLM service.
        """
        service = MagicMock(spec=LLMService)
        service.generate_completion = AsyncMock(return_value={"content": "This is a summary"})
        return service
    
    @pytest.fixture
    def mock_context_service(self):
        """
        Create a mock context service.
        """
        service = MagicMock()
        service.summarize_conversation_segment = MagicMock(return_value=MagicMock(id=1))
        service.add_summary_to_context = MagicMock(return_value=MagicMock())
        return service
    
    @pytest.fixture
    def summary_manager(self, mock_llm_service):
        """
        Create a summary manager.
        """
        return SummaryManager(mock_llm_service)
    
    @pytest.fixture
    def mock_messages(self):
        """
        Create mock messages.
        """
        return [
            MagicMock(
                spec=Message,
                id=1,
                role=MessageRole.USER,
                content="Hello, I need help with the hydraulic system on a Boeing 737."
            ),
            MagicMock(
                spec=Message,
                id=2,
                role=MessageRole.ASSISTANT,
                content="I'd be happy to help with the hydraulic system. What specific issue are you experiencing?"
            ),
            MagicMock(
                spec=Message,
                id=3,
                role=MessageRole.USER,
                content="The pressure is dropping during operation and I'm not sure what's causing it."
            ),
            MagicMock(
                spec=Message,
                id=4,
                role=MessageRole.ASSISTANT,
                content="Pressure drops in the hydraulic system can be caused by several issues. Let me help you troubleshoot."
            )
        ]
    
    @pytest.mark.asyncio
    async def test_process_conversation(self, summary_manager, mock_messages, mock_context_service):
        """
        Test processing a conversation.
        """
        # Mock should_summarize to return True
        with patch.object(ConversationSummarizer, 'should_summarize', return_value=True):
            # Mock identify_segments_for_summarization
            segments = [
                {
                    "start_idx": 0,
                    "end_idx": 1,
                    "start_message_id": 1,
                    "end_message_id": 2,
                    "messages": mock_messages[:2]
                }
            ]
            with patch.object(ConversationSummarizer, 'identify_segments_for_summarization', return_value=segments):
                # Mock summarize_messages
                with patch.object(ConversationSummarizer, 'summarize_messages', AsyncMock(return_value="This is a summary")):
                    # Call process_conversation
                    summaries = await summary_manager.process_conversation(
                        conversation_id=1,
                        messages=mock_messages,
                        context_service=mock_context_service
                    )
                    
                    # Verify result
                    assert len(summaries) == 1
                    
                    # Verify context_service methods were called
                    mock_context_service.summarize_conversation_segment.assert_called_once_with(
                        conversation_id=1,
                        start_message_id=1,
                        end_message_id=2,
                        summary_content="This is a summary"
                    )
                    mock_context_service.add_summary_to_context.assert_called_once()
