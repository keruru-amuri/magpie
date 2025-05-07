"""
Agent models for the MAGPIE platform.
"""
import enum
from typing import Optional, Dict, Any, Union

from sqlalchemy import (
    Boolean, Column, Enum, Float, Integer, String, Text
)

from app.models.base import BaseModel
from app.models.conversation import AgentType, JSONBType


class AgentResponse:
    """
    Standard response format for agent operations.
    """

    def __init__(
        self,
        success: bool,
        response: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an agent response.

        Args:
            success: Whether the operation was successful
            response: Human-readable response message
            data: Optional data payload
        """
        self.success = success
        self.response = response
        self.data = data


class ModelSize(str, enum.Enum):
    """
    Enum for model sizes.
    """

    SMALL = "small"  # gpt-4.1-nano
    MEDIUM = "medium"  # gpt-4.1-mini
    LARGE = "large"  # gpt-4.1


class AgentConfiguration(BaseModel):
    """
    Agent configuration model for storing agent settings.
    """

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    agent_type = Column(Enum(AgentType), nullable=False)
    model_size = Column(Enum(ModelSize), default=ModelSize.MEDIUM, nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    max_tokens = Column(Integer, default=4000, nullable=False)
    system_prompt = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    meta_data = Column(JSONBType, nullable=True)

    def __repr__(self) -> str:
        """
        String representation of the agent configuration.

        Returns:
            str: Agent configuration representation
        """
        return f"<AgentConfiguration {self.name} ({self.agent_type})>"
