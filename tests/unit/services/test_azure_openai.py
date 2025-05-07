"""Tests for Azure OpenAI client."""

import pytest
from unittest.mock import MagicMock, patch

from app.services.azure_openai import AzureOpenAIClient, get_azure_openai_client


class TestAzureOpenAIClient:
    """Tests for AzureOpenAIClient."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        with patch("app.services.azure_openai.settings") as mock_settings:
            # Set up mock settings
            mock_settings.AZURE_OPENAI_API_KEY = "test-api-key"
            mock_settings.AZURE_OPENAI_ENDPOINT = "https://test-endpoint.openai.azure.com/"
            mock_settings.AZURE_OPENAI_API_VERSION = "2023-12-01-preview"
            mock_settings.GPT_4_1_DEPLOYMENT_NAME = "gpt-4-1"
            mock_settings.GPT_4_1_MINI_DEPLOYMENT_NAME = "gpt-4-1-mini"
            mock_settings.GPT_4_1_NANO_DEPLOYMENT_NAME = "gpt-4-1-nano"

            # Initialize client
            client = AzureOpenAIClient()

            # Check that settings were used
            assert client.api_key == "test-api-key"
            assert client.endpoint == "https://test-endpoint.openai.azure.com/"
            assert client.api_version == "2023-12-01-preview"
            assert client.gpt_4_1_deployment == "gpt-4-1"
            assert client.gpt_4_1_mini_deployment == "gpt-4-1-mini"
            assert client.gpt_4_1_nano_deployment == "gpt-4-1-nano"

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        client = AzureOpenAIClient(
            api_key="custom-api-key",
            endpoint="https://custom-endpoint.openai.azure.com/",
            api_version="custom-api-version",
        )

        assert client.api_key == "custom-api-key"
        assert client.endpoint == "https://custom-endpoint.openai.azure.com/"
        assert client.api_version == "custom-api-version"

    def test_validate_configuration_missing_api_key(self):
        """Test validation with missing API key."""
        with patch("app.services.azure_openai.settings") as mock_settings:
            # Set up mock settings with empty API key
            mock_settings.AZURE_OPENAI_API_KEY = ""
            mock_settings.AZURE_OPENAI_ENDPOINT = "https://test.com"
            mock_settings.AZURE_OPENAI_API_VERSION = "v1"

            # Test with empty API key
            with pytest.raises(ValueError, match="Azure OpenAI API key is required"):
                client = AzureOpenAIClient()
                client._validate_configuration()

    def test_validate_configuration_missing_endpoint(self):
        """Test validation with missing endpoint."""
        with patch("app.services.azure_openai.settings") as mock_settings:
            # Set up mock settings with empty endpoint
            mock_settings.AZURE_OPENAI_API_KEY = "test-key"
            mock_settings.AZURE_OPENAI_ENDPOINT = ""
            mock_settings.AZURE_OPENAI_API_VERSION = "v1"

            # Test with empty endpoint
            with pytest.raises(ValueError, match="Azure OpenAI endpoint is required"):
                client = AzureOpenAIClient()
                client._validate_configuration()

    def test_validate_configuration_missing_api_version(self):
        """Test validation with missing API version."""
        with patch("app.services.azure_openai.settings") as mock_settings:
            # Set up mock settings with empty API version
            mock_settings.AZURE_OPENAI_API_KEY = "test-key"
            mock_settings.AZURE_OPENAI_ENDPOINT = "https://test.com"
            mock_settings.AZURE_OPENAI_API_VERSION = ""

            # Test with empty API version
            with pytest.raises(ValueError, match="Azure OpenAI API version is required"):
                client = AzureOpenAIClient()
                client._validate_configuration()

    def test_chat_completion(self):
        """Test chat completion."""
        with patch("app.services.azure_openai.AzureOpenAI") as mock_azure_openai:
            # Set up mock client
            mock_client = MagicMock()
            mock_azure_openai.return_value = mock_client

            # Set up mock response
            mock_response = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response

            # Initialize client
            client = AzureOpenAIClient(
                api_key="test-api-key",
                endpoint="https://test-endpoint.openai.azure.com/",
                api_version="2023-12-01-preview",
            )

            # Call chat completion
            messages = [{"role": "user", "content": "Hello"}]
            response = client.chat_completion(messages=messages)

            # Check that the client was called correctly
            mock_client.chat.completions.create.assert_called_once_with(
                model=client.gpt_4_1_deployment,
                messages=messages,
                temperature=0.7,
                max_tokens=None,
                stream=False,
            )

            # Check that the response was returned
            assert response == mock_response

    def test_get_model_by_size(self):
        """Test get_model_by_size."""
        with patch("app.services.azure_openai.settings") as mock_settings:
            # Set up mock settings
            mock_settings.AZURE_OPENAI_API_KEY = "test-api-key"
            mock_settings.AZURE_OPENAI_ENDPOINT = "https://test-endpoint.openai.azure.com/"
            mock_settings.AZURE_OPENAI_API_VERSION = "2023-12-01-preview"
            mock_settings.GPT_4_1_DEPLOYMENT_NAME = "gpt-4-1"
            mock_settings.GPT_4_1_MINI_DEPLOYMENT_NAME = "gpt-4-1-mini"
            mock_settings.GPT_4_1_NANO_DEPLOYMENT_NAME = "gpt-4-1-nano"

            # Initialize client
            client = AzureOpenAIClient()

            # Test small model
            assert client.get_model_by_size("small") == "gpt-4-1-nano"

            # Test medium model
            assert client.get_model_by_size("medium") == "gpt-4-1-mini"

            # Test large model
            assert client.get_model_by_size("large") == "gpt-4-1"

            # Test invalid model size
            with pytest.raises(ValueError, match="Invalid model size: invalid"):
                client.get_model_by_size("invalid")

    def test_get_azure_openai_client(self):
        """Test get_azure_openai_client."""
        # Clear the LRU cache to ensure our mock is used
        get_azure_openai_client.cache_clear()

        with patch("app.services.azure_openai.AzureOpenAIClient") as mock_client_class:
            # Set up mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Get client
            client = get_azure_openai_client()

            # Check that the client was created
            mock_client_class.assert_called_once()

            # Check that the client was returned
            assert client == mock_client
