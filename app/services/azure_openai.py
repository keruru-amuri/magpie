"""Azure OpenAI service for MAGPIE platform."""

import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from openai import AzureOpenAI, AsyncAzureOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class AzureOpenAIClient:
    """Client for Azure OpenAI API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        api_version: Optional[str] = None,
    ):
        """
        Initialize the Azure OpenAI client.

        Args:
            api_key: Azure OpenAI API key. Defaults to settings.AZURE_OPENAI_API_KEY.
            endpoint: Azure OpenAI endpoint. Defaults to settings.AZURE_OPENAI_ENDPOINT.
            api_version: Azure OpenAI API version. Defaults to settings.AZURE_OPENAI_API_VERSION.
        """
        self.api_key = api_key or settings.AZURE_OPENAI_API_KEY
        self.endpoint = endpoint or settings.AZURE_OPENAI_ENDPOINT
        self.api_version = api_version or settings.AZURE_OPENAI_API_VERSION

        # Validate configuration
        self._validate_configuration()

        # Initialize client with default configuration
        # Note: Removed proxies parameter which is not supported in OpenAI 1.12.0
        try:
            self.client = AzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version=self.api_version,
            )

            # Initialize async client
            self.async_client = AsyncAzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version=self.api_version,
            )
        except TypeError as e:
            # Log the error for debugging
            logger.warning(f"Error initializing OpenAI client: {str(e)}")
            logger.warning("Falling back to basic initialization")

            # Try with minimal parameters if there's a TypeError
            import httpx
            self.client = AzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version=self.api_version,
                http_client=httpx.Client(),
            )

            self.async_client = AsyncAzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version=self.api_version,
                http_client=httpx.AsyncClient(),
            )

        # Model deployment names
        self.gpt_4_1_deployment = settings.GPT_4_1_DEPLOYMENT_NAME
        self.gpt_4_1_mini_deployment = settings.GPT_4_1_MINI_DEPLOYMENT_NAME
        self.gpt_4_1_nano_deployment = settings.GPT_4_1_NANO_DEPLOYMENT_NAME

        logger.info(f"Azure OpenAI client initialized with endpoint: {self.endpoint}")

    def _validate_configuration(self) -> None:
        """
        Validate the Azure OpenAI configuration.

        Raises:
            ValueError: If any required configuration is missing.
        """
        if self.api_key is None or self.api_key == "":
            raise ValueError("Azure OpenAI API key is required")
        if self.endpoint is None or self.endpoint == "":
            raise ValueError("Azure OpenAI endpoint is required")
        if self.api_version is None or self.api_version == "":
            raise ValueError("Azure OpenAI API version is required")

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate a chat completion using Azure OpenAI.

        Args:
            messages: List of messages in the conversation.
            model: Model deployment name. Defaults to GPT-4.1.
            temperature: Temperature for sampling. Defaults to 0.7.
            max_tokens: Maximum number of tokens to generate. Defaults to None.
            stream: Whether to stream the response. Defaults to False.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Chat completion response.

        Raises:
            Exception: If the API call fails.
        """
        try:
            # Use the specified model or default to GPT-4.1
            deployment_name = model or self.gpt_4_1_deployment

            logger.debug(f"Sending chat completion request to model: {deployment_name}")

            # Make the API call
            response = self.client.chat.completions.create(
                model=deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs,
            )

            # Log success
            logger.debug(f"Chat completion successful with model: {deployment_name}")

            # Return the response
            return response
        except Exception as e:
            # Log the error
            logger.error(f"Chat completion failed: {str(e)}")
            # Re-raise the exception for retry
            raise

    async def async_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate a chat completion asynchronously using Azure OpenAI.

        Args:
            messages: List of messages in the conversation.
            model: Model deployment name. Defaults to GPT-4.1.
            temperature: Temperature for sampling. Defaults to 0.7.
            max_tokens: Maximum number of tokens to generate. Defaults to None.
            stream: Whether to stream the response. Defaults to False.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Chat completion response.

        Raises:
            Exception: If the API call fails.
        """
        try:
            # Use the specified model or default to GPT-4.1
            deployment_name = model or self.gpt_4_1_deployment

            logger.debug(f"Sending async chat completion request to model: {deployment_name}")

            # Make the API call
            response = await self.async_client.chat.completions.create(
                model=deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs,
            )

            # Log success
            logger.debug(f"Async chat completion successful with model: {deployment_name}")

            # Return the response
            return response
        except Exception as e:
            # Log the error
            logger.error(f"Async chat completion failed: {str(e)}")
            # Raise the exception
            raise

    def get_model_by_size(self, size: str) -> str:
        """
        Get the model deployment name by size.

        Args:
            size: Model size (small, medium, large).

        Returns:
            Model deployment name.

        Raises:
            ValueError: If the size is invalid.
        """
        size = size.lower()
        if size == "small":
            return self.gpt_4_1_nano_deployment
        elif size == "medium":
            return self.gpt_4_1_mini_deployment
        elif size == "large":
            return self.gpt_4_1_deployment
        else:
            raise ValueError(f"Invalid model size: {size}")


@lru_cache()
def get_azure_openai_client() -> AzureOpenAIClient:
    """
    Get the Azure OpenAI client.

    If mock data is enabled, returns a mock client.
    Otherwise, returns a real client.

    Returns:
        Azure OpenAI client.
    """
    try:
        # Check if mock data is enabled
        from app.core.mock.config import get_mock_data_config
        mock_config = get_mock_data_config()

        if mock_config.use_mock_data:
            # Import and use mock client
            logger.info("Using mock Azure OpenAI client")
            from app.services.mock_azure_openai import get_mock_azure_openai_client
            return get_mock_azure_openai_client()
    except ImportError:
        # If mock module is not available, continue with real client
        logger.warning("Mock module not available, using real Azure OpenAI client")
    except Exception as e:
        # Log any other errors but continue with real client
        logger.warning(f"Error checking mock configuration: {str(e)}")

    # Use real client
    logger.info("Using real Azure OpenAI client")
    return AzureOpenAIClient()
