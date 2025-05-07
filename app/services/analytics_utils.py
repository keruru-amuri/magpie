"""
Utilities for tracking analytics in the MAGPIE platform.

This module provides utilities for tracking token usage and costs.
"""

import logging
from enum import Enum
from typing import Dict, Optional

from app.core.monitoring import ModelSize as AnalyticsModelSize
from app.core.monitoring import record_usage


# Define model sizes to match LLM service
class LLMModelSize(str, Enum):
    """Model size enum."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

# Configure logging
logger = logging.getLogger(__name__)


# Map LLM service model sizes to analytics model sizes
MODEL_SIZE_MAP = {
    LLMModelSize.SMALL: AnalyticsModelSize.SMALL,
    LLMModelSize.MEDIUM: AnalyticsModelSize.MEDIUM,
    LLMModelSize.LARGE: AnalyticsModelSize.LARGE,
}


def track_llm_usage(
    usage: Dict[str, int],
    model_size: LLMModelSize,
    agent_type: str,
    user_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    request_id: Optional[str] = None,
    latency_ms: Optional[float] = None,
) -> None:
    """
    Track LLM usage for analytics.

    Args:
        usage: Token usage information from the LLM response.
        model_size: Size of the model used.
        agent_type: Type of agent that used the model.
        user_id: ID of the user who made the request.
        conversation_id: ID of the conversation.
        request_id: ID of the request.
        latency_ms: Latency of the request in milliseconds.
    """
    try:
        # Extract token counts
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        # Map model size
        analytics_model_size = MODEL_SIZE_MAP.get(model_size, AnalyticsModelSize.MEDIUM)

        # Record usage
        record_usage(
            model_size=analytics_model_size,
            agent_type=agent_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            user_id=user_id,
            conversation_id=conversation_id,
            request_id=request_id,
            latency_ms=latency_ms,
        )

        logger.debug(
            f"Tracked LLM usage: {input_tokens} input tokens, {output_tokens} output tokens, "
            f"model: {model_size}, agent: {agent_type}"
        )
    except Exception as e:
        # Log error but don't raise exception to avoid affecting the main flow
        logger.error(f"Failed to track LLM usage: {str(e)}")
