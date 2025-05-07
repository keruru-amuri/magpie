"""
Orchestrator endpoints for MAGPIE platform.

This module provides API endpoints for the centralized orchestrator
that routes user requests to the appropriate specialized agent.
"""
import logging
import uuid
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.db.connection import get_db
from app.core.orchestrator import Orchestrator
from app.models.conversation import AgentType
from app.models.orchestrator import OrchestratorRequest, OrchestratorResponse
from app.repositories.agent import AgentConfigurationRepository
from app.repositories.conversation import ConversationRepository
from app.services.llm_service import LLMService

# Configure logging
logger = logging.getLogger(__name__)
router = APIRouter()


class QueryRequest(BaseModel):
    """
    Query request model for the orchestrator endpoint.
    """

    query: str = Field(..., description="User query to process")
    user_id: str = Field(..., description="User ID for tracking and personalization")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context continuity")
    context: Optional[Dict[str, str]] = Field(None, description="Additional context for the query")
    metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata for the query")
    force_agent_type: Optional[AgentType] = Field(None, description="Force routing to a specific agent type")
    enable_multi_agent: Optional[bool] = Field(True, description="Enable multi-agent responses for complex queries")


class RoutingInfoResponse(BaseModel):
    """
    Response model for routing information.
    """

    agent_type: AgentType = Field(..., description="Selected agent type")
    confidence: float = Field(..., description="Confidence score for the classification")
    reasoning: str = Field(..., description="Reasoning for the classification")
    requires_followup: bool = Field(..., description="Whether the query requires followup")
    requires_multiple_agents: bool = Field(..., description="Whether the query requires multiple agents")
    additional_agent_types: Optional[List[AgentType]] = Field(None, description="Additional agent types for complex queries")


class ConversationHistoryItem(BaseModel):
    """
    Model for a conversation history item.
    """

    role: str = Field(..., description="Role (user or assistant)")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp")
    agent_type: Optional[AgentType] = Field(None, description="Agent type for assistant messages")


class ConversationHistoryResponse(BaseModel):
    """
    Response model for conversation history.
    """

    conversation_id: str = Field(..., description="Conversation ID")
    messages: List[ConversationHistoryItem] = Field(..., description="Conversation messages")


# Dependency to get the orchestrator
async def get_orchestrator(db=Depends(get_db)):
    """
    Get the orchestrator instance.

    Args:
        db: Database session

    Returns:
        Orchestrator: Orchestrator instance
    """
    llm_service = LLMService()
    agent_repository = AgentConfigurationRepository(db)
    conversation_repository = ConversationRepository(db)

    orchestrator = Orchestrator(
        llm_service=llm_service,
        agent_repository=agent_repository,
        conversation_repository=conversation_repository
    )

    await orchestrator.initialize()
    return orchestrator


@router.post(
    "/query",
    response_model=OrchestratorResponse,
    summary="Process a query through the orchestrator",
    tags=["orchestrator"],
    description="Process a user query through the centralized orchestrator, which will analyze the query, "
                "route it to the appropriate agent, and return the response."
)
async def process_query(
    request: QueryRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Process a query through the orchestrator.

    The orchestrator will:
    1. Analyze the query to determine the appropriate agent
    2. Route the query to the selected agent
    3. Return the agent's response

    Args:
        request: Query request
        orchestrator: Orchestrator instance

    Returns:
        OrchestratorResponse: Orchestrator response
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())

        # Convert request to OrchestratorRequest
        orchestrator_request = OrchestratorRequest(
            query=request.query,
            user_id=request.user_id,
            conversation_id=conversation_id,
            context=request.context,
            metadata=request.metadata
        )

        # Add force_agent_type to metadata if provided
        if request.force_agent_type:
            if not orchestrator_request.metadata:
                orchestrator_request.metadata = {}
            orchestrator_request.metadata["force_agent_type"] = request.force_agent_type.value

        # Add enable_multi_agent to metadata
        if orchestrator_request.metadata is None:
            orchestrator_request.metadata = {}
        orchestrator_request.metadata["enable_multi_agent"] = str(request.enable_multi_agent)

        # Process the request
        response = await orchestrator.process_request(orchestrator_request)

        return response

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@router.get(
    "/routing-info",
    response_model=RoutingInfoResponse,
    summary="Get routing information for a query without processing it",
    tags=["orchestrator"],
    description="Analyze a query to determine the appropriate agent type and routing information "
                "without actually processing the query."
)
async def get_routing_info(
    query: str = Query(..., description="User query to analyze"),
    conversation_id: Optional[str] = Query(None, description="Conversation ID for context"),
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Get routing information for a query without processing it.

    Args:
        query: User query to analyze
        conversation_id: Optional conversation ID for context
        orchestrator: Orchestrator instance

    Returns:
        RoutingInfoResponse: Routing information
    """
    try:
        # Get conversation history if available
        conversation_history = None
        if conversation_id and orchestrator.conversation_repository:
            conversation_history = await orchestrator._get_conversation_history(conversation_id)

        # Classify the request
        classification = await orchestrator.classifier.classify_request(
            query=query,
            available_agents=orchestrator.agent_registry.get_all_agents(),
            conversation_history=conversation_history
        )

        # Route the request (but don't process it)
        routing_result = await orchestrator.router.route_request(
            classification=classification,
            conversation_id=conversation_id,
            query=query
        )

        # Convert to response model
        return RoutingInfoResponse(
            agent_type=routing_result.agent_type,
            confidence=classification.confidence,
            reasoning=classification.reasoning,
            requires_followup=routing_result.requires_followup,
            requires_multiple_agents=routing_result.requires_multiple_agents,
            additional_agent_types=routing_result.additional_agent_types
        )

    except Exception as e:
        logger.error(f"Error getting routing info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting routing info: {str(e)}"
        )


@router.get(
    "/conversation/{conversation_id}",
    response_model=ConversationHistoryResponse,
    summary="Get conversation history",
    tags=["orchestrator"],
    description="Get the conversation history for a specific conversation ID."
)
async def get_conversation_history(
    conversation_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Get conversation history.

    Args:
        conversation_id: Conversation ID
        orchestrator: Orchestrator instance

    Returns:
        ConversationHistoryResponse: Conversation history
    """
    try:
        if not orchestrator.conversation_repository:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Conversation repository not available"
            )

        # Get messages from the conversation repository
        messages = orchestrator.conversation_repository.get_messages(conversation_id)

        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )

        # Convert to response model
        history_items = []
        for message in messages:
            agent_type = None
            if message.metadata and "agent_type" in message.metadata:
                try:
                    agent_type = AgentType(message.metadata["agent_type"])
                except ValueError:
                    pass

            history_items.append(
                ConversationHistoryItem(
                    role=message.role,
                    content=message.content,
                    timestamp=message.timestamp.isoformat() if message.timestamp else "",
                    agent_type=agent_type
                )
            )

        return ConversationHistoryResponse(
            conversation_id=conversation_id,
            messages=history_items
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting conversation history: {str(e)}"
        )


@router.delete(
    "/conversation/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation history",
    tags=["orchestrator"],
    description="Delete the conversation history for a specific conversation ID."
)
async def delete_conversation_history(
    conversation_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Delete conversation history.

    Args:
        conversation_id: Conversation ID
        orchestrator: Orchestrator instance
    """
    try:
        if not orchestrator.conversation_repository:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Conversation repository not available"
            )

        # Delete conversation from the repository
        success = orchestrator.conversation_repository.delete_conversation(conversation_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )

        # Clear routing history for this conversation
        orchestrator.router.clear_routing_history(conversation_id)

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting conversation history: {str(e)}"
        )
