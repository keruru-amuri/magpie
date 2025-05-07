"""LLM service for MAGPIE platform."""

import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from app.services.analytics_utils import track_llm_usage
from app.services.azure_openai import get_azure_openai_client
from app.services.exceptions import AzureOpenAIError, map_openai_error
from app.services.prompt_templates import get_template
from app.services.response_parser import parse_chat_completion
from app.services.token_utils import truncate_messages_to_token_limit

# Configure logging
logger = logging.getLogger(__name__)


class ModelSize(str, Enum):
    """Model size enum."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class LLMService:
    """LLM service for MAGPIE platform."""

    def __init__(self):
        """Initialize the LLM service."""
        self.client = get_azure_openai_client()

    def generate_response(
        self,
        template_name: str,
        variables: Dict[str, Any],
        model_size: ModelSize = ModelSize.MEDIUM,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate a response using a template.

        Args:
            template_name: Name of the template to use.
            variables: Variables to format the template with.
            model_size: Size of the model to use.
            temperature: Temperature for sampling.
            max_tokens: Maximum number of tokens to generate.
            stream: Whether to stream the response.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Response from the LLM.

        Raises:
            ValueError: If the template is not found.
            AzureOpenAIError: If the API call fails.
        """
        try:
            # Get the template
            template = get_template(template_name)

            # Format the template
            messages = template.format(**variables)

            # Truncate messages if needed
            if max_tokens:
                messages = truncate_messages_to_token_limit(
                    messages,
                    max_tokens=max_tokens,
                    preserve_system_message=True,
                    preserve_last_messages=1,
                )

            # Get the model deployment name
            model = self.client.get_model_by_size(model_size)

            # Generate the response
            response = self.client.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs,
            )

            # Parse the response
            parsed_response = parse_chat_completion(response)

            # Get usage information
            usage = parsed_response.get_token_usage()

            # Track usage for analytics
            track_llm_usage(
                usage=usage,
                model_size=model_size,
                agent_type="template",
                user_id=kwargs.get("user_id"),
                conversation_id=kwargs.get("conversation_id"),
                request_id=kwargs.get("request_id"),
                latency_ms=None,
            )

            return {
                "response": parsed_response,
                "content": parsed_response.get_message_content(),
                "usage": usage,
            }
        except ValueError as e:
            logger.error(f"Template error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"LLM service error: {str(e)}")
            raise map_openai_error(e)

    async def generate_response_async(
        self,
        template_name: str,
        variables: Dict[str, Any],
        model_size: ModelSize = ModelSize.MEDIUM,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate a response asynchronously using a template.

        Args:
            template_name: Name of the template to use.
            variables: Variables to format the template with.
            model_size: Size of the model to use.
            temperature: Temperature for sampling.
            max_tokens: Maximum number of tokens to generate.
            stream: Whether to stream the response.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Response from the LLM.

        Raises:
            ValueError: If the template is not found.
            AzureOpenAIError: If the API call fails.
        """
        try:
            # Get the template
            template = get_template(template_name)

            # Format the template
            messages = template.format(**variables)

            # Truncate messages if needed
            if max_tokens:
                messages = truncate_messages_to_token_limit(
                    messages,
                    max_tokens=max_tokens,
                    preserve_system_message=True,
                    preserve_last_messages=1,
                )

            # Get the model deployment name
            model = self.client.get_model_by_size(model_size)

            # Generate the response
            response = await self.client.async_chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs,
            )

            # Parse the response
            parsed_response = parse_chat_completion(response)

            # Get usage information
            usage = parsed_response.get_token_usage()

            # Track usage for analytics
            track_llm_usage(
                usage=usage,
                model_size=model_size,
                agent_type="template_async",
                user_id=kwargs.get("user_id"),
                conversation_id=kwargs.get("conversation_id"),
                request_id=kwargs.get("request_id"),
                latency_ms=None,
            )

            return {
                "response": parsed_response,
                "content": parsed_response.get_message_content(),
                "usage": usage,
            }
        except ValueError as e:
            logger.error(f"Template error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"LLM service error: {str(e)}")
            raise map_openai_error(e)

    def generate_custom_response(
        self,
        messages: List[Dict[str, str]],
        model_size: ModelSize = ModelSize.MEDIUM,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate a response using custom messages.

        Args:
            messages: List of messages.
            model_size: Size of the model to use.
            temperature: Temperature for sampling.
            max_tokens: Maximum number of tokens to generate.
            stream: Whether to stream the response.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Response from the LLM.

        Raises:
            AzureOpenAIError: If the API call fails.
        """
        try:
            # Truncate messages if needed
            if max_tokens:
                messages = truncate_messages_to_token_limit(
                    messages,
                    max_tokens=max_tokens,
                    preserve_system_message=True,
                    preserve_last_messages=1,
                )

            # Get the model deployment name
            model = self.client.get_model_by_size(model_size)

            # Generate the response
            response = self.client.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs,
            )

            # Parse the response
            parsed_response = parse_chat_completion(response)

            # Get usage information
            usage = parsed_response.get_token_usage()

            # Track usage for analytics
            track_llm_usage(
                usage=usage,
                model_size=model_size,
                agent_type="custom",
                user_id=kwargs.get("user_id"),
                conversation_id=kwargs.get("conversation_id"),
                request_id=kwargs.get("request_id"),
                latency_ms=None,
            )

            return {
                "response": parsed_response,
                "content": parsed_response.get_message_content(),
                "usage": usage,
            }
        except Exception as e:
            logger.error(f"LLM service error: {str(e)}")
            raise map_openai_error(e)

    async def generate_custom_response_async(
        self,
        messages: List[Dict[str, str]],
        model_size: ModelSize = ModelSize.MEDIUM,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate a response asynchronously using custom messages.

        Args:
            messages: List of messages.
            model_size: Size of the model to use.
            temperature: Temperature for sampling.
            max_tokens: Maximum number of tokens to generate.
            stream: Whether to stream the response.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Response from the LLM.

        Raises:
            AzureOpenAIError: If the API call fails.
        """
        try:
            # Truncate messages if needed
            if max_tokens:
                messages = truncate_messages_to_token_limit(
                    messages,
                    max_tokens=max_tokens,
                    preserve_system_message=True,
                    preserve_last_messages=1,
                )

            # Get the model deployment name
            model = self.client.get_model_by_size(model_size)

            # Generate the response
            response = await self.client.async_chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs,
            )

            # Parse the response
            parsed_response = parse_chat_completion(response)

            # Get usage information
            usage = parsed_response.get_token_usage()

            # Track usage for analytics
            track_llm_usage(
                usage=usage,
                model_size=model_size,
                agent_type="custom_async",
                user_id=kwargs.get("user_id"),
                conversation_id=kwargs.get("conversation_id"),
                request_id=kwargs.get("request_id"),
                latency_ms=None,
            )

            return {
                "response": parsed_response,
                "content": parsed_response.get_message_content(),
                "usage": usage,
            }
        except Exception as e:
            logger.error(f"LLM service error: {str(e)}")
            raise map_openai_error(e)


# Create a singleton instance
llm_service = LLMService()
