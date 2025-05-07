"""
Main orchestrator for the MAGPIE platform.

This module provides the central orchestration functionality for routing
user requests to the appropriate specialized agent based on the content
and intent of the request.
"""
import logging
import uuid
from typing import Dict, List, Optional

from app.core.model_selection.complexity import ComplexityAnalyzer
from app.core.model_selection.selector import ModelSelector
from app.core.orchestrator.classifier import RequestClassifier
from app.core.orchestrator.formatter import ResponseFormatter
from app.core.orchestrator.registry import AgentRegistry
from app.core.orchestrator.router import Router
from app.models.agent import ModelSize
from app.models.conversation import AgentType
from app.models.orchestrator import (
    OrchestratorRequest,
    OrchestratorResponse,
    RequestClassification,
    RoutingResult,
)
from app.repositories.agent import AgentConfigurationRepository
from app.repositories.conversation import ConversationRepository
from app.services.llm_service import LLMService

# Configure logging
logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Central orchestrator for routing requests to appropriate agents.
    """

    def __init__(
        self,
        llm_service: LLMService,
        agent_repository: AgentConfigurationRepository,
        conversation_repository: Optional[ConversationRepository] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            llm_service: LLM service for classification and agent responses
            agent_repository: Repository for agent configurations
            conversation_repository: Optional repository for conversation history
        """
        self.llm_service = llm_service
        self.agent_repository = agent_repository
        self.conversation_repository = conversation_repository

        # Initialize components
        self.classifier = RequestClassifier(llm_service)
        self.agent_registry = AgentRegistry(agent_repository)
        self.router = Router(self.agent_registry)
        self.formatter = ResponseFormatter()

        # Initialize model selection components
        self.complexity_analyzer = ComplexityAnalyzer(llm_service)
        self.model_selector = ModelSelector(self.complexity_analyzer)

        # Initialize registry
        self._registry_initialized = False

    async def initialize(self) -> None:
        """
        Initialize the orchestrator by loading agent configurations.
        """
        if not self._registry_initialized:
            await self.agent_registry.initialize()
            self._registry_initialized = True
            logger.info("Orchestrator initialized successfully")

    async def process_request(self, request: OrchestratorRequest) -> OrchestratorResponse:
        """
        Process a user request and route it to the appropriate agent.

        Args:
            request: Orchestrator request

        Returns:
            OrchestratorResponse: Orchestrator response
        """
        try:
            # Ensure orchestrator is initialized
            if not self._registry_initialized:
                await self.initialize()

            # Get conversation history if available
            conversation_history = None
            if self.conversation_repository and request.conversation_id:
                conversation_history = await self._get_conversation_history(request.conversation_id)

            # Classify the request
            classification = await self.classifier.classify_request(
                query=request.query,
                available_agents=self.agent_registry.get_all_agents(),
                conversation_history=conversation_history
            )

            # Route the request
            routing_result = await self.router.route_request(
                classification=classification,
                conversation_id=request.conversation_id
            )

            # Get agent configuration
            agent_config = self.agent_repository.get_by_id(routing_result.agent_config_id)
            if not agent_config:
                raise ValueError(f"Agent configuration not found: {routing_result.agent_config_id}")

            # Generate response from the agent
            agent_response = await self._generate_agent_response(
                query=request.query,
                agent_config=agent_config,
                conversation_history=conversation_history,
                context=request.context
            )

            # Format the response
            conversation_id = request.conversation_id or str(uuid.uuid4())
            formatted_response = self.formatter.format_response(
                response_content=agent_response,
                agent_type=agent_config.agent_type,
                agent_name=agent_config.name,
                confidence=classification.confidence,
                conversation_id=conversation_id,
                metadata=request.metadata
            )

            # Save conversation if repository is available
            if self.conversation_repository:
                await self._save_conversation(
                    user_id=request.user_id,
                    conversation_id=conversation_id,
                    query=request.query,
                    response=formatted_response.response,
                    agent_type=agent_config.agent_type
                )

            return formatted_response

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            # Return a fallback response
            return OrchestratorResponse(
                response="I apologize, but there was an error processing your request. Please try again.",
                agent_type=AgentType.DOCUMENTATION,
                agent_name="Error Handler",
                confidence=0.0,
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                metadata={"error": str(e)} if request.metadata is None else {**request.metadata, "error": str(e)},
                followup_questions=None
            )

    async def _generate_agent_response(
        self,
        query: str,
        agent_config,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Generate a response from an agent.

        Args:
            query: User query
            agent_config: Agent configuration
            conversation_history: Optional conversation history
            context: Optional additional context

        Returns:
            str: Agent response
        """
        try:
            # Create system prompt based on agent type and configuration
            system_prompt = agent_config.system_prompt or self._get_default_system_prompt(agent_config.agent_type)

            # Add context if available
            if context:
                context_str = "\n\nAdditional context:\n"
                for key, value in context.items():
                    context_str += f"{key}: {value}\n"
                system_prompt += context_str

            # Prepare messages
            messages = [{"role": "system", "content": system_prompt}]

            # Add conversation history if available
            if conversation_history:
                for message in conversation_history:
                    messages.append(message)

            # Add the current query
            messages.append({"role": "user", "content": query})

            # Select the appropriate model based on query complexity
            model_size = agent_config.model_size  # Default from agent config

            # Use model selection system if available
            try:
                # Analyze query complexity and select model
                selected_model, complexity_score = await self.model_selector.select_model(
                    query=query,
                    conversation_history=conversation_history,
                    cost_sensitive=context.get("cost_sensitive", False) if context else False,
                    performance_sensitive=context.get("performance_sensitive", False) if context else False
                )

                # Override model size if complexity analysis suggests a different model
                if selected_model:
                    model_size = selected_model.size
                    logger.info(
                        f"Model selection: {model_size} (complexity: {complexity_score.level}, "
                        f"score: {complexity_score.overall_score:.2f})"
                    )
            except Exception as model_selection_error:
                # Log error but continue with default model size
                logger.warning(f"Model selection failed, using default: {str(model_selection_error)}")

            # Generate response
            response = await self.llm_service.generate_custom_response_async(
                messages=messages,
                model_size=model_size,
                temperature=agent_config.temperature,
                max_tokens=agent_config.max_tokens
            )

            return response["content"]

        except Exception as e:
            logger.error(f"Error generating agent response: {str(e)}")
            raise

    def _get_default_system_prompt(self, agent_type: AgentType) -> str:
        """
        Get the default system prompt for an agent type.

        Args:
            agent_type: Agent type

        Returns:
            str: Default system prompt
        """
        if agent_type == AgentType.DOCUMENTATION:
            return (
                "You are a helpful aircraft maintenance documentation assistant. "
                "Your role is to help technicians and engineers find relevant information in technical documentation. "
                "Provide clear, concise answers based on the available documentation. "
                "If you don't know the answer, say so clearly and suggest where the information might be found."
            )
        elif agent_type == AgentType.TROUBLESHOOTING:
            return (
                "You are a helpful aircraft troubleshooting advisor. "
                "Your role is to help technicians and engineers diagnose and resolve issues with aircraft systems. "
                "Provide step-by-step troubleshooting guidance based on the symptoms described. "
                "Consider safety implications and regulatory requirements in your recommendations."
            )
        elif agent_type == AgentType.MAINTENANCE:
            return (
                "You are a helpful aircraft maintenance procedure generator. "
                "Your role is to help technicians and engineers create step-by-step maintenance procedures. "
                "Ensure procedures are clear, comprehensive, and follow industry best practices. "
                "Include safety precautions, required tools, and reference relevant documentation."
            )
        else:
            return (
                "You are a helpful assistant for aircraft maintenance, repair, and overhaul. "
                "Provide clear, accurate information to help users with their queries. "
                "If you don't know the answer, say so clearly."
            )

    async def _get_conversation_history(self, conversation_id: str) -> Optional[List[Dict[str, str]]]:
        """
        Get conversation history for a conversation ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Optional[List[Dict[str, str]]]: Conversation history or None
        """
        if not self.conversation_repository:
            return None

        try:
            # Get messages from the conversation
            messages = self.conversation_repository.get_messages(conversation_id)

            # Convert to the format expected by the LLM service
            history = []
            for message in messages:
                role = "assistant" if message.role == "assistant" else "user"
                history.append({"role": role, "content": message.content})

            return history

        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return None

    async def _save_conversation(
        self,
        user_id: str,
        conversation_id: str,
        query: str,
        response: str,
        agent_type: AgentType,
    ) -> None:
        """
        Save a conversation to the repository.

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            query: User query
            response: Agent response
            agent_type: Agent type
        """
        if not self.conversation_repository:
            return

        try:
            # Save the conversation
            self.conversation_repository.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                content=query,
                role="user"
            )

            self.conversation_repository.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                content=response,
                role="assistant",
                metadata={"agent_type": agent_type.value}
            )

        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}")
            # Don't raise the exception, as this is a non-critical operation
