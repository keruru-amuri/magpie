"""Tests for LLM service."""

import pytest
from unittest.mock import MagicMock, patch

from app.services.llm_service import LLMService, ModelSize


class TestLLMService:
    """Tests for LLMService."""

    def test_init(self):
        """Test initialization."""
        with patch("app.services.llm_service.get_azure_openai_client") as mock_get_client:
            # Set up mock client
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            # Initialize service
            service = LLMService()

            # Check that the client was retrieved
            mock_get_client.assert_called_once()

            # Check that the client was set
            assert service.client == mock_client

    def test_generate_response(self):
        """Test generate_response."""
        with patch("app.services.llm_service.get_template") as mock_get_template, \
             patch("app.services.llm_service.truncate_messages_to_token_limit") as mock_truncate, \
             patch("app.services.llm_service.parse_chat_completion") as mock_parse:
            # Set up mock template
            mock_template = MagicMock()
            mock_template.format.return_value = [{"role": "user", "content": "Test message"}]
            mock_get_template.return_value = mock_template

            # Set up mock truncate
            mock_truncate.return_value = [{"role": "user", "content": "Truncated message"}]

            # Set up mock client
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_client.chat_completion.return_value = mock_response
            mock_client.get_model_by_size.return_value = "gpt-4-1"

            # Set up mock parse
            mock_parsed_response = MagicMock()
            mock_parsed_response.get_message_content.return_value = "Test response"
            mock_parsed_response.get_token_usage.return_value = {"total_tokens": 100}
            mock_parse.return_value = mock_parsed_response

            # Initialize service
            service = LLMService()
            service.client = mock_client

            # Call generate_response
            response = service.generate_response(
                template_name="test_template",
                variables={"key": "value"},
                model_size=ModelSize.MEDIUM,
                temperature=0.5,
                max_tokens=100,
            )

            # Check that the template was retrieved and formatted
            mock_get_template.assert_called_once_with("test_template")
            mock_template.format.assert_called_once_with(key="value")

            # Check that the messages were truncated
            mock_truncate.assert_called_once_with(
                [{"role": "user", "content": "Test message"}],
                max_tokens=100,
                preserve_system_message=True,
                preserve_last_messages=1,
            )

            # Check that the model was retrieved
            mock_client.get_model_by_size.assert_called_once_with(ModelSize.MEDIUM)

            # Check that the client was called
            mock_client.chat_completion.assert_called_once_with(
                messages=[{"role": "user", "content": "Truncated message"}],
                model="gpt-4-1",
                temperature=0.5,
                max_tokens=100,
                stream=False,
            )

            # Check that the response was parsed
            mock_parse.assert_called_once_with(mock_response)

            # Check that the response was returned
            assert response["response"] == mock_parsed_response
            assert response["content"] == "Test response"
            assert response["usage"] == {"total_tokens": 100}

    def test_generate_response_error(self):
        """Test generate_response with error."""
        with patch("app.services.llm_service.get_template") as mock_get_template, \
             patch("app.services.llm_service.map_openai_error") as mock_map_error:
            # Set up mock template
            mock_template = MagicMock()
            mock_template.format.side_effect = ValueError("Test error")
            mock_get_template.return_value = mock_template

            # Set up mock map_error
            mock_error = MagicMock()
            mock_map_error.return_value = mock_error

            # Initialize service
            service = LLMService()

            # Call generate_response
            with pytest.raises(ValueError, match="Test error"):
                service.generate_response(
                    template_name="test_template",
                    variables={"key": "value"},
                )

            # Check that the template was retrieved
            mock_get_template.assert_called_once_with("test_template")

            # Check that map_error was not called
            mock_map_error.assert_not_called()

    def test_generate_custom_response(self):
        """Test generate_custom_response."""
        with patch("app.services.llm_service.truncate_messages_to_token_limit") as mock_truncate, \
             patch("app.services.llm_service.parse_chat_completion") as mock_parse:
            # Set up mock truncate
            mock_truncate.return_value = [{"role": "user", "content": "Truncated message"}]

            # Set up mock client
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_client.chat_completion.return_value = mock_response
            mock_client.get_model_by_size.return_value = "gpt-4-1"

            # Set up mock parse
            mock_parsed_response = MagicMock()
            mock_parsed_response.get_message_content.return_value = "Test response"
            mock_parsed_response.get_token_usage.return_value = {"total_tokens": 100}
            mock_parse.return_value = mock_parsed_response

            # Initialize service
            service = LLMService()
            service.client = mock_client

            # Call generate_custom_response
            response = service.generate_custom_response(
                messages=[{"role": "user", "content": "Test message"}],
                model_size=ModelSize.MEDIUM,
                temperature=0.5,
                max_tokens=100,
            )

            # Check that the messages were truncated
            mock_truncate.assert_called_once_with(
                [{"role": "user", "content": "Test message"}],
                max_tokens=100,
                preserve_system_message=True,
                preserve_last_messages=1,
            )

            # Check that the model was retrieved
            mock_client.get_model_by_size.assert_called_once_with(ModelSize.MEDIUM)

            # Check that the client was called
            mock_client.chat_completion.assert_called_once_with(
                messages=[{"role": "user", "content": "Truncated message"}],
                model="gpt-4-1",
                temperature=0.5,
                max_tokens=100,
                stream=False,
            )

            # Check that the response was parsed
            mock_parse.assert_called_once_with(mock_response)

            # Check that the response was returned
            assert response["response"] == mock_parsed_response
            assert response["content"] == "Test response"
            assert response["usage"] == {"total_tokens": 100}

    def test_generate_custom_response_error(self):
        """Test generate_custom_response with error."""
        with patch("app.services.llm_service.map_openai_error") as mock_map_error:
            # Set up mock client
            mock_client = MagicMock()
            mock_client.chat_completion.side_effect = Exception("Test error")
            mock_client.get_model_by_size.return_value = "gpt-4-1"

            # Set up mock map_error
            mock_error = MagicMock()
            mock_map_error.return_value = mock_error

            # Initialize service
            service = LLMService()
            service.client = mock_client

            # Call generate_custom_response
            with pytest.raises(Exception):
                service.generate_custom_response(
                    messages=[{"role": "user", "content": "Test message"}],
                )

            # Check that map_error was called
            mock_map_error.assert_called_once()
