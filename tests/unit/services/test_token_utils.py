"""Tests for token utilities."""

import pytest

from app.services.token_utils import (
    count_tokens_approximate,
    count_message_tokens,
    truncate_messages_to_token_limit,
)


class TestTokenUtils:
    """Tests for token utilities."""

    def test_count_tokens_approximate(self):
        """Test count_tokens_approximate."""
        # Test empty string
        assert count_tokens_approximate("") == 0

        # Test simple string
        text = "This is a test."
        assert count_tokens_approximate(text) > 0

        # Test longer string
        text = "This is a longer test with more words and characters."
        assert count_tokens_approximate(text) > count_tokens_approximate("This is a test.")

    def test_count_message_tokens(self):
        """Test count_message_tokens."""
        # Test empty list
        assert count_message_tokens([]) == 0

        # Test single message
        messages = [{"role": "user", "content": "This is a test."}]
        assert count_message_tokens(messages) > 0

        # Test multiple messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "This is a test."},
            {"role": "assistant", "content": "I'm here to help."},
        ]
        assert count_message_tokens(messages) > count_message_tokens([{"role": "user", "content": "This is a test."}])

    def test_truncate_messages_to_token_limit(self):
        """Test truncate_messages_to_token_limit."""
        # Test empty list
        assert truncate_messages_to_token_limit([]) == []

        # Test list with system message and user message
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "This is a test."},
        ]
        truncated = truncate_messages_to_token_limit(messages, max_tokens=1000)
        assert len(truncated) == 2
        assert truncated[0]["role"] == "system"
        assert truncated[1]["role"] == "user"

        # Test list with system message and multiple user/assistant messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "Question 2"},
            {"role": "assistant", "content": "Answer 2"},
            {"role": "user", "content": "Question 3"},
        ]
        truncated = truncate_messages_to_token_limit(
            messages, max_tokens=100, preserve_system_message=True, preserve_last_messages=1
        )
        # Should preserve system message and last user message
        assert truncated[0]["role"] == "system"
        assert truncated[-1]["content"] == "Question 3"

        # Test with very low token limit
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "This is a test."},
        ]
        truncated = truncate_messages_to_token_limit(messages, max_tokens=1)
        # Should return an empty list or just the system message
        assert len(truncated) <= 1
