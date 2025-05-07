"""
Agent factory for the MAGPIE platform.
"""
import logging
from typing import Dict, Optional, Any

from app.models.conversation import AgentType
from app.services.llm_service import LLMService
from app.core.agents.documentation_agent import DocumentationAgent
from app.core.agents.troubleshooting_agent import TroubleshootingAgent
from app.core.agents.maintenance_agent import MaintenanceAgent

# Configure logging
logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory for creating agent instances.
    """

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        documentation_service: Optional[Any] = None,
        troubleshooting_service: Optional[Any] = None,
        maintenance_service: Optional[Any] = None
    ):
        """
        Initialize agent factory.

        Args:
            llm_service: LLM service for generating responses
            documentation_service: Service for accessing documentation
            troubleshooting_service: Service for accessing troubleshooting data
            maintenance_service: Service for accessing maintenance data
        """
        self.llm_service = llm_service or LLMService()
        self.documentation_service = documentation_service
        self.troubleshooting_service = troubleshooting_service
        self.maintenance_service = maintenance_service
        
        # Import services if not provided
        if not self.documentation_service or not self.troubleshooting_service or not self.maintenance_service:
            from app.core.mock.service import mock_data_service
            
            if not self.documentation_service:
                self.documentation_service = mock_data_service
            
            if not self.troubleshooting_service:
                self.troubleshooting_service = mock_data_service
            
            if not self.maintenance_service:
                self.maintenance_service = mock_data_service

    def create_agent(self, agent_type: AgentType) -> Any:
        """
        Create an agent instance.

        Args:
            agent_type: Type of agent to create

        Returns:
            Agent instance

        Raises:
            ValueError: If agent type is not supported
        """
        if agent_type == AgentType.DOCUMENTATION:
            return DocumentationAgent(
                llm_service=self.llm_service,
                documentation_service=self.documentation_service
            )
        elif agent_type == AgentType.TROUBLESHOOTING:
            return TroubleshootingAgent(
                llm_service=self.llm_service,
                troubleshooting_service=self.troubleshooting_service
            )
        elif agent_type == AgentType.MAINTENANCE:
            return MaintenanceAgent(
                llm_service=self.llm_service,
                maintenance_service=self.maintenance_service
            )
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")

    def create_agent_for_config(self, agent_config: Dict[str, Any]) -> Any:
        """
        Create an agent instance from a configuration.

        Args:
            agent_config: Agent configuration

        Returns:
            Agent instance

        Raises:
            ValueError: If agent type is not supported
        """
        agent_type = agent_config.get("agent_type")
        if not agent_type:
            raise ValueError("Agent configuration must include 'agent_type'")
        
        # Convert string to enum if needed
        if isinstance(agent_type, str):
            try:
                agent_type = AgentType(agent_type)
            except ValueError:
                raise ValueError(f"Invalid agent type: {agent_type}")
        
        # Create agent
        agent = self.create_agent(agent_type)
        
        # Configure agent if needed
        # This is where we would apply any additional configuration
        
        return agent
