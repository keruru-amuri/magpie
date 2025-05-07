"""Mock Azure OpenAI service for MAGPIE platform."""

import logging
import json
import random
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from app.core.config import settings
from app.core.mock.config import get_mock_data_config

# Configure logging
logger = logging.getLogger(__name__)


class MockAzureOpenAIClient:
    """Mock client for Azure OpenAI API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        api_version: Optional[str] = None,
    ):
        """
        Initialize the mock Azure OpenAI client.

        Args:
            api_key: Azure OpenAI API key. Defaults to settings.AZURE_OPENAI_API_KEY.
            endpoint: Azure OpenAI endpoint. Defaults to settings.AZURE_OPENAI_ENDPOINT.
            api_version: Azure OpenAI API version. Defaults to settings.AZURE_OPENAI_API_VERSION.
        """
        self.api_key = api_key or settings.AZURE_OPENAI_API_KEY
        self.endpoint = endpoint or settings.AZURE_OPENAI_ENDPOINT
        self.api_version = api_version or settings.AZURE_OPENAI_API_VERSION

        # Model deployment names
        self.gpt_4_1_deployment = settings.GPT_4_1_DEPLOYMENT_NAME
        self.gpt_4_1_mini_deployment = settings.GPT_4_1_MINI_DEPLOYMENT_NAME
        self.gpt_4_1_nano_deployment = settings.GPT_4_1_NANO_DEPLOYMENT_NAME

        logger.info("Mock Azure OpenAI client initialized")

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
        Generate a mock chat completion.

        Args:
            messages: List of messages in the conversation.
            model: Model deployment name. Defaults to GPT-4.1.
            temperature: Temperature for sampling. Defaults to 0.7.
            max_tokens: Maximum number of tokens to generate. Defaults to None.
            stream: Whether to stream the response. Defaults to False.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Mock chat completion response.
        """
        try:
            # Use the specified model or default to GPT-4.1
            deployment_name = model or self.gpt_4_1_deployment

            logger.debug(f"Sending mock chat completion request to model: {deployment_name}")

            # Get the last user message
            user_message = None
            for message in reversed(messages):
                if message.get("role") == "user":
                    user_message = message.get("content", "")
                    break

            # Generate a mock response
            response_content = self._generate_mock_response(user_message, deployment_name)

            # Create a mock response object
            response = {
                "id": f"chatcmpl-{self._generate_id()}",
                "object": "chat.completion",
                "created": int(datetime.now().timestamp()),
                "model": deployment_name,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_content,
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": self._estimate_tokens(messages),
                    "completion_tokens": self._estimate_tokens([{"content": response_content}]),
                    "total_tokens": self._estimate_tokens(messages) + self._estimate_tokens([{"content": response_content}]),
                },
            }

            # Log success
            logger.debug(f"Mock chat completion successful with model: {deployment_name}")

            # Return the response
            return response
        except Exception as e:
            # Log the error
            logger.error(f"Mock chat completion failed: {str(e)}")
            # Re-raise the exception
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
        Generate a mock chat completion asynchronously.

        Args:
            messages: List of messages in the conversation.
            model: Model deployment name. Defaults to GPT-4.1.
            temperature: Temperature for sampling. Defaults to 0.7.
            max_tokens: Maximum number of tokens to generate. Defaults to None.
            stream: Whether to stream the response. Defaults to False.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Mock chat completion response.
        """
        # Just call the synchronous method for simplicity
        return self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs,
        )

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

    def _generate_id(self) -> str:
        """
        Generate a random ID.

        Returns:
            Random ID.
        """
        return f"{random.randint(1000000, 9999999)}-{random.randint(1000000, 9999999)}"

    def _estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        Estimate the number of tokens in a list of messages.

        Args:
            messages: List of messages.

        Returns:
            Estimated number of tokens.
        """
        total_tokens = 0
        for message in messages:
            content = message.get("content", "")
            if content:
                # Rough estimate: 1 token per 4 characters
                total_tokens += len(content) // 4
        return max(1, total_tokens)

    def _generate_mock_response(self, user_message: Optional[str], model: str) -> str:
        """
        Generate a mock response based on the user message.

        Args:
            user_message: User message.
            model: Model deployment name.

        Returns:
            Mock response.
        """
        if not user_message:
            return "I'm not sure what you're asking. Could you please provide more details?"

        # Sample responses for different types of queries
        documentation_responses = [
            "According to the maintenance manual, this procedure requires special tooling. The specific tools needed are: calibrated torque wrench (5-20 Nm), safety wire pliers, and a digital multimeter.",
            "The technical documentation indicates that this component has a service life of 5,000 flight hours or 3 years, whichever comes first. You should check the maintenance records to verify the installation date.",
            "Based on the aircraft type you mentioned, the relevant section in the AMM is 32-41-00. This covers the complete landing gear inspection procedure including all required checks and measurements.",
        ]

        troubleshooting_responses = [
            "Based on the symptoms you've described, this could be related to the hydraulic pressure sensor. I recommend checking the electrical connections first, then verifying the sensor calibration using the procedure in AMM 29-21-05.",
            "This intermittent warning light is typically caused by a loose connector in the landing gear assembly. Check connector J42 on the main gear control unit for corrosion or pin damage.",
            "The fault code you're seeing (FC-2103) indicates a problem with the environmental control system. This is commonly caused by a failed temperature sensor or blocked air filter.",
        ]

        maintenance_responses = [
            "Here's the procedure for replacing that component:\n1. Ensure aircraft power is off\n2. Access the component through panel A-123\n3. Disconnect electrical connectors\n4. Remove mounting bolts (torque: 15 Nm)\n5. Install new component\n6. Reconnect electrical connectors\n7. Perform functional test according to AMM 24-34-05",
            "For this maintenance task, you'll need the following tools:\n- 10mm socket wrench\n- Torque wrench (5-20 Nm)\n- Multimeter\n- Safety wire pliers\n- Calibrated pressure gauge (0-100 psi)",
            "After completing this maintenance task, you'll need to perform a leak check using the following procedure:\n1. Pressurize the system to 65 psi\n2. Apply leak detection fluid to all connections\n3. Check for bubbles indicating leaks\n4. Depressurize system\n5. Clean all components with approved solvent",
        ]

        # Determine the type of response based on the user message
        user_message_lower = user_message.lower()
        if any(keyword in user_message_lower for keyword in ["manual", "document", "documentation", "reference"]):
            responses = documentation_responses
        elif any(keyword in user_message_lower for keyword in ["problem", "issue", "troubleshoot", "error", "fault", "warning"]):
            responses = troubleshooting_responses
        else:
            responses = maintenance_responses

        # Return a random response
        return random.choice(responses)


@lru_cache()
def get_mock_azure_openai_client() -> MockAzureOpenAIClient:
    """
    Get the mock Azure OpenAI client.

    Returns:
        Mock Azure OpenAI client.
    """
    return MockAzureOpenAIClient()
