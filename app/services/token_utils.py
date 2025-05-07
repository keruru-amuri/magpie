"""Token utilities for Azure OpenAI service."""

import logging
import re
from typing import Dict, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

# Default tokens per character ratio for approximation
DEFAULT_TOKENS_PER_CHAR = 0.25


def count_tokens_approximate(text: str) -> int:
    """
    Count the approximate number of tokens in a text.

    This is a simple approximation based on the average number of tokens per word.
    For more accurate token counting, use the tiktoken library.

    Args:
        text: Text to count tokens for.

    Returns:
        Approximate number of tokens.
    """
    if not text:
        return 0

    # Split the text into words
    words = re.findall(r'\w+', text)

    # Approximate token count (4 characters per token on average)
    token_count = len(words) + len(text) // 4

    # Ensure at least 1 token for non-empty text
    return max(1, token_count)


def count_tokens_openai(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens using OpenAI's tokenizer.

    Args:
        text: Text to count tokens for
        model: Model name to use for tokenization

    Returns:
        int: Token count
    """
    try:
        import tiktoken

        # Get encoding for model
        encoding = tiktoken.encoding_for_model(model)

        # Count tokens
        tokens = encoding.encode(text)
        return len(tokens)
    except ImportError:
        logger.warning("tiktoken not installed, using approximate token count")
        return count_tokens_approximate(text)
    except Exception as e:
        logger.error(f"Error counting tokens with tiktoken: {str(e)}")
        return count_tokens_approximate(text)


def count_tokens_azure(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens using Azure OpenAI's tokenizer.

    This is a wrapper around count_tokens_openai that maps Azure model names
    to OpenAI model names.

    Args:
        text: Text to count tokens for
        model: Azure model name

    Returns:
        int: Token count
    """
    # Map Azure model names to OpenAI model names
    model_map = {
        "gpt-4": "gpt-4",
        "gpt-4-32k": "gpt-4-32k",
        "gpt-35-turbo": "gpt-3.5-turbo",
        "gpt-35-turbo-16k": "gpt-3.5-turbo-16k",
        "gpt-4-1106-preview": "gpt-4-1106-preview",
        "gpt-4-vision-preview": "gpt-4-vision-preview",
        "gpt-4.1": "gpt-4-1106-preview",
        "gpt-4.1-mini": "gpt-4-1106-preview",
        "gpt-4.1-nano": "gpt-3.5-turbo"
    }

    # Map model name
    openai_model = model_map.get(model, model)

    # Count tokens
    return count_tokens_openai(text, openai_model)


def count_message_tokens(messages: List[Dict[str, str]]) -> int:
    """
    Count the approximate number of tokens in a list of messages.

    Args:
        messages: List of messages.

    Returns:
        Approximate number of tokens.
    """
    total_tokens = 0

    for message in messages:
        # Add tokens for message role (approximate)
        total_tokens += 4

        # Add tokens for message content
        content = message.get("content", "")
        if isinstance(content, str):
            total_tokens += count_tokens_approximate(content)

    # Add tokens for message formatting (approximate)
    total_tokens += 2 * len(messages)

    return total_tokens


def truncate_text_to_token_limit(text: str, max_tokens: int, model: str = "gpt-4") -> str:
    """
    Truncate text to fit within token limit.

    Args:
        text: Text to truncate
        max_tokens: Maximum number of tokens
        model: Model name to use for tokenization

    Returns:
        str: Truncated text
    """
    if not text:
        return ""

    # Count tokens
    token_count = count_tokens_azure(text, model)

    # Check if truncation is needed
    if token_count <= max_tokens:
        return text

    # Simple truncation based on character count
    # This is approximate and may not be exact
    char_ratio = len(text) / token_count
    char_limit = int(max_tokens * char_ratio)

    # Truncate text
    truncated_text = text[:char_limit]

    # Add ellipsis
    truncated_text += "..."

    return truncated_text


def truncate_messages_to_token_limit(
    messages: List[Dict[str, str]],
    max_tokens: int = 4000,
    preserve_system_message: bool = True,
    preserve_last_messages: int = 2,
) -> List[Dict[str, str]]:
    """
    Truncate a list of messages to fit within a token limit.

    Args:
        messages: List of messages.
        max_tokens: Maximum number of tokens.
        preserve_system_message: Whether to preserve the system message.
        preserve_last_messages: Number of most recent messages to preserve.

    Returns:
        Truncated list of messages.
    """
    if not messages:
        return []

    # Make a copy of the messages
    messages_copy = messages.copy()

    # Extract system message if present and if we want to preserve it
    system_message = None
    if preserve_system_message and messages_copy and messages_copy[0].get("role") == "system":
        system_message = messages_copy.pop(0)

    # Extract last N messages to preserve
    last_messages = messages_copy[-preserve_last_messages:] if preserve_last_messages > 0 else []
    messages_copy = messages_copy[:-preserve_last_messages] if preserve_last_messages > 0 else messages_copy

    # Calculate tokens for system message and last messages
    system_tokens = count_tokens_approximate(system_message.get("content", "")) + 4 if system_message else 0
    last_messages_tokens = count_message_tokens(last_messages)

    # Calculate remaining tokens
    remaining_tokens = max_tokens - system_tokens - last_messages_tokens

    # If remaining tokens is negative, we need to truncate the last messages
    if remaining_tokens < 0:
        logger.warning("Not enough tokens to preserve system message and last messages")
        # Try to preserve at least the system message
        if system_message:
            remaining_tokens = max_tokens - system_tokens
            if remaining_tokens < 0:
                logger.warning("Not enough tokens to preserve system message")
                return []

        # Try to preserve as many of the last messages as possible
        preserved_last_messages = []
        for message in reversed(last_messages):
            message_tokens = count_tokens_approximate(message.get("content", "")) + 4
            if remaining_tokens - message_tokens >= 0:
                preserved_last_messages.insert(0, message)
                remaining_tokens -= message_tokens
            else:
                break

        result = []
        if system_message:
            result.append(system_message)
        result.extend(preserved_last_messages)
        return result

    # Add messages from the middle until we reach the token limit
    middle_messages = []
    for message in messages_copy:
        message_tokens = count_tokens_approximate(message.get("content", "")) + 4
        if remaining_tokens - message_tokens >= 0:
            middle_messages.append(message)
            remaining_tokens -= message_tokens
        else:
            break

    # Combine all parts
    result = []
    if system_message:
        result.append(system_message)
    result.extend(middle_messages)
    result.extend(last_messages)

    return result
