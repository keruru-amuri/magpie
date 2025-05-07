"""
Context summarization for the MAGPIE platform.
"""
import logging
from typing import Dict, List, Optional, Union, Any

from app.models.context import ContextSummary, ContextPriority
from app.models.conversation import Message, MessageRole
from app.services.llm_service import LLMService
from app.services.prompt_templates import CONVERSATION_SUMMARY_TEMPLATE
from app.services.token_utils import count_tokens_azure, truncate_text_to_token_limit

# Configure logging
logger = logging.getLogger(__name__)


class ConversationSummarizer:
    """
    Summarize conversations using LLM.
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize conversation summarizer.

        Args:
            llm_service: LLM service for summarization
        """
        self.llm_service = llm_service or LLMService()

    async def summarize_messages(
        self,
        messages: List[Message],
        max_summary_tokens: int = 500,
        model: str = "gpt-4.1-mini"
    ) -> Optional[str]:
        """
        Summarize a list of messages.

        Args:
            messages: List of messages to summarize
            max_summary_tokens: Maximum tokens for the summary
            model: Model to use for summarization

        Returns:
            Optional[str]: Summary text or None if error
        """
        try:
            if not messages:
                logger.warning("No messages to summarize")
                return None

            # Format messages for summarization
            formatted_messages = self._format_messages_for_summarization(messages)

            # Check if we need to truncate the conversation
            conversation_text = "\n".join(formatted_messages)
            max_input_tokens = 4000  # Reserve tokens for the prompt and response
            if count_tokens_azure(conversation_text, model) > max_input_tokens:
                conversation_text = truncate_text_to_token_limit(
                    conversation_text, max_input_tokens, model
                )

            # Create prompt for summarization
            prompt_variables = {
                "conversation": conversation_text
            }

            # Generate summary
            response = await self.llm_service.generate_completion(
                prompt_template=CONVERSATION_SUMMARY_TEMPLATE,
                variables=prompt_variables,
                model=model,
                max_tokens=max_summary_tokens
            )

            if not response or not response.get("content"):
                logger.error("Failed to generate summary")
                return None

            return response["content"]
        except Exception as e:
            logger.error(f"Error summarizing messages: {str(e)}")
            return None

    def _format_messages_for_summarization(self, messages: List[Message]) -> List[str]:
        """
        Format messages for summarization.

        Args:
            messages: List of messages to format

        Returns:
            List[str]: Formatted messages
        """
        formatted_messages = []
        for message in messages:
            role_prefix = ""
            if message.role == MessageRole.USER:
                role_prefix = "User: "
            elif message.role == MessageRole.ASSISTANT:
                role_prefix = "Assistant: "
            elif message.role == MessageRole.SYSTEM:
                role_prefix = "System: "
            else:
                role_prefix = f"{message.role}: "

            formatted_messages.append(f"{role_prefix}{message.content}")

        return formatted_messages

    def should_summarize(
        self,
        messages: List[Message],
        token_threshold: int = 3000,
        message_count_threshold: int = 20
    ) -> bool:
        """
        Determine if a conversation should be summarized.

        Args:
            messages: List of messages
            token_threshold: Token threshold for summarization
            message_count_threshold: Message count threshold for summarization

        Returns:
            bool: True if the conversation should be summarized
        """
        if not messages:
            return False

        # Check message count
        if len(messages) >= message_count_threshold:
            return True

        # Check token count
        total_tokens = sum(
            count_tokens_azure(message.content or "", "gpt-4.1-mini")
            for message in messages
        )
        if total_tokens >= token_threshold:
            return True

        return False

    def identify_segments_for_summarization(
        self,
        messages: List[Message],
        segment_size: int = 10,
        overlap: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Identify segments of a conversation for summarization.

        Args:
            messages: List of messages
            segment_size: Number of messages per segment
            overlap: Number of messages to overlap between segments

        Returns:
            List[Dict[str, Any]]: List of segments with start and end indices
        """
        if not messages or len(messages) <= segment_size:
            return []

        segments = []
        i = 0
        while i < len(messages):
            end_idx = min(i + segment_size, len(messages))
            segments.append({
                "start_idx": i,
                "end_idx": end_idx - 1,
                "start_message_id": messages[i].id,
                "end_message_id": messages[end_idx - 1].id,
                "messages": messages[i:end_idx]
            })
            i += segment_size - overlap

        return segments


class SummaryManager:
    """
    Manage conversation summaries.
    """

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        token_threshold: int = 3000,
        message_count_threshold: int = 20,
        segment_size: int = 10,
        overlap: int = 2
    ):
        """
        Initialize summary manager.

        Args:
            llm_service: LLM service for summarization
            token_threshold: Token threshold for summarization
            message_count_threshold: Message count threshold for summarization
            segment_size: Number of messages per segment
            overlap: Number of messages to overlap between segments
        """
        self.summarizer = ConversationSummarizer(llm_service)
        self.token_threshold = token_threshold
        self.message_count_threshold = message_count_threshold
        self.segment_size = segment_size
        self.overlap = overlap

    async def process_conversation(
        self,
        conversation_id: Union[int, str],
        messages: List[Message],
        context_service: Any
    ) -> List[ContextSummary]:
        """
        Process a conversation for summarization.

        Args:
            conversation_id: Conversation ID
            messages: List of messages
            context_service: Context service for creating summaries

        Returns:
            List[ContextSummary]: List of created summaries
        """
        try:
            # Check if summarization is needed
            if not self.summarizer.should_summarize(
                messages,
                self.token_threshold,
                self.message_count_threshold
            ):
                return []

            # Identify segments for summarization
            segments = self.summarizer.identify_segments_for_summarization(
                messages,
                self.segment_size,
                self.overlap
            )

            if not segments:
                return []

            # Summarize each segment
            summaries = []
            for segment in segments:
                # Generate summary
                summary_text = await self.summarizer.summarize_messages(
                    segment["messages"]
                )

                if not summary_text:
                    continue

                # Create summary in database
                summary = context_service.summarize_conversation_segment(
                    conversation_id=conversation_id,
                    start_message_id=segment["start_message_id"],
                    end_message_id=segment["end_message_id"],
                    summary_content=summary_text
                )

                if summary:
                    # Add summary to context
                    context_service.add_summary_to_context(
                        summary_id=summary.id,
                        conversation_id=conversation_id,
                        priority=ContextPriority.HIGH
                    )
                    summaries.append(summary)

            return summaries
        except Exception as e:
            logger.error(f"Error processing conversation for summarization: {str(e)}")
            return []
