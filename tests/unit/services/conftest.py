"""Fixtures for services tests."""

import pytest
from unittest.mock import MagicMock, patch

from app.services.azure_openai import AzureOpenAIClient


@pytest.fixture
def mock_azure_openai_client():
    """Mock Azure OpenAI client."""
    with patch("app.services.azure_openai.AzureOpenAI"), \
         patch("app.services.azure_openai.AsyncAzureOpenAI"), \
         patch("app.services.azure_openai.settings") as mock_settings:
        # Set up mock settings
        mock_settings.AZURE_OPENAI_API_KEY = "test-api-key"
        mock_settings.AZURE_OPENAI_ENDPOINT = "https://test-endpoint.openai.azure.com/"
        mock_settings.AZURE_OPENAI_API_VERSION = "2023-12-01-preview"
        mock_settings.GPT_4_1_DEPLOYMENT_NAME = "gpt-4-1"
        mock_settings.GPT_4_1_MINI_DEPLOYMENT_NAME = "gpt-4-1-mini"
        mock_settings.GPT_4_1_NANO_DEPLOYMENT_NAME = "gpt-4-1-nano"

        # Create client
        client = AzureOpenAIClient()

        # Mock chat_completion method
        client.chat_completion = MagicMock()
        client.async_chat_completion = MagicMock()

        yield client
