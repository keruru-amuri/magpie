"""
Orchestrator models for the MAGPIE platform.
"""
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.models.conversation import AgentType


class ClassificationConfidence(float, Enum):
    """
    Enum for classification confidence levels.
    """

    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.9


class RequestClassification(BaseModel):
    """
    Model for request classification results.
    """

    agent_type: AgentType
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    
    @property
    def confidence_level(self) -> ClassificationConfidence:
        """
        Get the confidence level based on the confidence score.
        
        Returns:
            ClassificationConfidence: Confidence level
        """
        if self.confidence >= ClassificationConfidence.HIGH:
            return ClassificationConfidence.HIGH
        elif self.confidence >= ClassificationConfidence.MEDIUM:
            return ClassificationConfidence.MEDIUM
        else:
            return ClassificationConfidence.LOW


class AgentCapability(BaseModel):
    """
    Model for agent capabilities.
    """

    name: str
    description: str
    keywords: List[str]
    examples: List[str]


class AgentMetadata(BaseModel):
    """
    Model for agent metadata.
    """

    agent_type: AgentType
    name: str
    description: str
    capabilities: List[AgentCapability]
    config_id: Optional[int] = None
    is_default: bool = False
    additional_info: Optional[Dict[str, str]] = None


class RoutingResult(BaseModel):
    """
    Model for routing results.
    """

    agent_type: AgentType
    agent_config_id: int
    classification: RequestClassification
    fallback_agent_config_id: Optional[int] = None
    requires_followup: bool = False
    requires_multiple_agents: bool = False
    additional_agent_types: Optional[List[AgentType]] = None


class OrchestratorRequest(BaseModel):
    """
    Model for orchestrator requests.
    """

    query: str
    user_id: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, str]] = None


class OrchestratorResponse(BaseModel):
    """
    Model for orchestrator responses.
    """

    response: str
    agent_type: AgentType
    agent_name: str
    confidence: float
    conversation_id: str
    metadata: Optional[Dict[str, str]] = None
    followup_questions: Optional[List[str]] = None
