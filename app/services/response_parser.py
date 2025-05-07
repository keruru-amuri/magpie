"""Response parser for Azure OpenAI service."""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, ValidationError

# Configure logging
logger = logging.getLogger(__name__)


class ChatCompletionResponse(BaseModel):
    """Model for chat completion response."""

    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

    def get_message_content(self) -> str:
        """
        Get the content of the first message in the response.

        Returns:
            Message content.
        """
        if not self.choices:
            return ""

        message = self.choices[0].get("message", {})
        return message.get("content", "")

    def get_token_usage(self) -> Dict[str, int]:
        """
        Get token usage information.

        Returns:
            Token usage information.
        """
        return self.usage


def parse_chat_completion(response: Any) -> ChatCompletionResponse:
    """
    Parse a chat completion response.

    Args:
        response: Chat completion response.

    Returns:
        Parsed response.

    Raises:
        ValueError: If the response is invalid.
    """
    try:
        # Convert response to dict if it's not already
        if not isinstance(response, dict):
            response_dict = response.model_dump() if hasattr(response, "model_dump") else response.__dict__
        else:
            response_dict = response

        # Parse the response
        return ChatCompletionResponse(**response_dict)
    except ValidationError as e:
        logger.error(f"Failed to parse chat completion response: {str(e)}")
        raise ValueError(f"Invalid chat completion response: {str(e)}")
    except Exception as e:
        logger.error(f"Error parsing chat completion response: {str(e)}")
        raise ValueError(f"Error parsing chat completion response: {str(e)}")


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from text.

    Args:
        text: Text containing JSON.

    Returns:
        Extracted JSON or None if no JSON is found.
    """
    # Try to find JSON in the text
    try:
        # Look for JSON between triple backticks
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", text)
        if json_match:
            json_str = json_match.group(1)
            return json.loads(json_str)

        # Look for JSON between curly braces
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)

        # Try to parse the entire text as JSON
        return json.loads(text)
    except (json.JSONDecodeError, AttributeError):
        return None


def extract_list_from_text(text: str) -> Optional[List[Any]]:
    """
    Extract a list from text.

    Args:
        text: Text containing a list.

    Returns:
        Extracted list or None if no list is found.
    """
    # Try to find a list in the text
    try:
        # Look for a list between triple backticks
        list_match = re.search(r"```json\s*([\s\S]*?)\s*```", text)
        if list_match:
            list_str = list_match.group(1)
            return json.loads(list_str)

        # Look for a list between square brackets
        list_match = re.search(r"\[[\s\S]*\]", text)
        if list_match:
            list_str = list_match.group(0)
            return json.loads(list_str)

        # Try to parse the entire text as a list
        return json.loads(text)
    except (json.JSONDecodeError, AttributeError):
        return None
