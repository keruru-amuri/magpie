"""Tests for response parser."""

import pytest
from unittest.mock import MagicMock

from app.services.response_parser import (
    ChatCompletionResponse,
    parse_chat_completion,
    extract_json_from_text,
    extract_list_from_text,
)


class TestResponseParser:
    """Tests for response parser."""

    def test_chat_completion_response(self):
        """Test ChatCompletionResponse."""
        response = ChatCompletionResponse(
            id="test-id",
            object="chat.completion",
            created=1234567890,
            model="gpt-4-1",
            choices=[
                {
                    "message": {
                        "role": "assistant",
                        "content": "Test content",
                    },
                    "index": 0,
                    "finish_reason": "stop",
                }
            ],
            usage={
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        )

        assert response.id == "test-id"
        assert response.object == "chat.completion"
        assert response.created == 1234567890
        assert response.model == "gpt-4-1"
        assert len(response.choices) == 1
        assert response.choices[0]["message"]["content"] == "Test content"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 20
        assert response.usage["total_tokens"] == 30

    def test_chat_completion_response_get_message_content(self):
        """Test ChatCompletionResponse.get_message_content."""
        response = ChatCompletionResponse(
            id="test-id",
            object="chat.completion",
            created=1234567890,
            model="gpt-4-1",
            choices=[
                {
                    "message": {
                        "role": "assistant",
                        "content": "Test content",
                    },
                    "index": 0,
                    "finish_reason": "stop",
                }
            ],
            usage={
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        )

        assert response.get_message_content() == "Test content"

        # Test with empty choices
        response.choices = []
        assert response.get_message_content() == ""

    def test_chat_completion_response_get_token_usage(self):
        """Test ChatCompletionResponse.get_token_usage."""
        response = ChatCompletionResponse(
            id="test-id",
            object="chat.completion",
            created=1234567890,
            model="gpt-4-1",
            choices=[
                {
                    "message": {
                        "role": "assistant",
                        "content": "Test content",
                    },
                    "index": 0,
                    "finish_reason": "stop",
                }
            ],
            usage={
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        )

        assert response.get_token_usage() == {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        }

    def test_parse_chat_completion(self):
        """Test parse_chat_completion."""
        # Test with dict
        response_dict = {
            "id": "test-id",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4-1",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Test content",
                    },
                    "index": 0,
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        }
        response = parse_chat_completion(response_dict)
        assert isinstance(response, ChatCompletionResponse)
        assert response.id == "test-id"
        assert response.get_message_content() == "Test content"

        # Test with object with model_dump method
        mock_response = MagicMock()
        mock_response.model_dump.return_value = response_dict
        response = parse_chat_completion(mock_response)
        assert isinstance(response, ChatCompletionResponse)
        assert response.id == "test-id"
        assert response.get_message_content() == "Test content"

        # Test with object with __dict__ attribute
        mock_response = MagicMock()
        mock_response.model_dump = None
        mock_response.__dict__ = response_dict
        response = parse_chat_completion(mock_response)
        assert isinstance(response, ChatCompletionResponse)
        assert response.id == "test-id"
        assert response.get_message_content() == "Test content"

    def test_parse_chat_completion_invalid(self):
        """Test parse_chat_completion with invalid response."""
        # Test with invalid dict
        with pytest.raises(ValueError, match="Invalid chat completion response"):
            parse_chat_completion({"invalid": "response"})

        # Test with exception
        with pytest.raises(ValueError, match="Error parsing chat completion response"):
            parse_chat_completion(123)  # Not a dict or object

    def test_extract_json_from_text(self):
        """Test extract_json_from_text."""
        # Test with JSON between triple backticks
        text = "Here is some JSON:\n```json\n{\"key\": \"value\"}\n```"
        json_data = extract_json_from_text(text)
        assert json_data == {"key": "value"}

        # Test with JSON between curly braces
        text = "Here is some JSON: {\"key\": \"value\"}"
        json_data = extract_json_from_text(text)
        assert json_data == {"key": "value"}

        # Test with entire text as JSON
        text = "{\"key\": \"value\"}"
        json_data = extract_json_from_text(text)
        assert json_data == {"key": "value"}

        # Test with invalid JSON
        text = "This is not JSON"
        json_data = extract_json_from_text(text)
        assert json_data is None

    def test_extract_list_from_text(self):
        """Test extract_list_from_text."""
        # Test with list between triple backticks
        text = "Here is a list:\n```json\n[1, 2, 3]\n```"
        list_data = extract_list_from_text(text)
        assert list_data == [1, 2, 3]

        # Test with list between square brackets
        text = "Here is a list: [1, 2, 3]"
        list_data = extract_list_from_text(text)
        assert list_data == [1, 2, 3]

        # Test with entire text as list
        text = "[1, 2, 3]"
        list_data = extract_list_from_text(text)
        assert list_data == [1, 2, 3]

        # Test with invalid list
        text = "This is not a list"
        list_data = extract_list_from_text(text)
        assert list_data is None
