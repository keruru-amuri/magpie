"""
Unit tests for the AgentFactory.
"""
import pytest
from unittest.mock import MagicMock

from app.models.conversation import AgentType
from app.core.agents.factory import AgentFactory
from app.core.agents.documentation_agent import DocumentationAgent
from app.core.agents.troubleshooting_agent import TroubleshootingAgent
from app.core.agents.maintenance_agent import MaintenanceAgent


class TestAgentFactory:
    """
    Test the AgentFactory class.
    """
    
    @pytest.fixture
    def mock_llm_service(self):
        """
        Create a mock LLM service.
        """
        return MagicMock()
    
    @pytest.fixture
    def mock_documentation_service(self):
        """
        Create a mock documentation service.
        """
        return MagicMock()
    
    @pytest.fixture
    def mock_troubleshooting_service(self):
        """
        Create a mock troubleshooting service.
        """
        return MagicMock()
    
    @pytest.fixture
    def mock_maintenance_service(self):
        """
        Create a mock maintenance service.
        """
        return MagicMock()
    
    @pytest.fixture
    def factory(
        self,
        mock_llm_service,
        mock_documentation_service,
        mock_troubleshooting_service,
        mock_maintenance_service
    ):
        """
        Create an AgentFactory instance.
        """
        return AgentFactory(
            llm_service=mock_llm_service,
            documentation_service=mock_documentation_service,
            troubleshooting_service=mock_troubleshooting_service,
            maintenance_service=mock_maintenance_service
        )
    
    def test_create_documentation_agent(self, factory):
        """
        Test creating a documentation agent.
        """
        # Create agent
        agent = factory.create_agent(AgentType.DOCUMENTATION)
        
        # Verify agent type
        assert isinstance(agent, DocumentationAgent)
        assert agent.llm_service == factory.llm_service
        assert agent.documentation_service == factory.documentation_service
    
    def test_create_troubleshooting_agent(self, factory):
        """
        Test creating a troubleshooting agent.
        """
        # Create agent
        agent = factory.create_agent(AgentType.TROUBLESHOOTING)
        
        # Verify agent type
        assert isinstance(agent, TroubleshootingAgent)
        assert agent.llm_service == factory.llm_service
        assert agent.troubleshooting_service == factory.troubleshooting_service
    
    def test_create_maintenance_agent(self, factory):
        """
        Test creating a maintenance agent.
        """
        # Create agent
        agent = factory.create_agent(AgentType.MAINTENANCE)
        
        # Verify agent type
        assert isinstance(agent, MaintenanceAgent)
        assert agent.llm_service == factory.llm_service
        assert agent.maintenance_service == factory.maintenance_service
    
    def test_create_agent_invalid_type(self, factory):
        """
        Test creating an agent with an invalid type.
        """
        # Create an invalid agent type
        class InvalidAgentType:
            pass
        
        # Verify ValueError is raised
        with pytest.raises(ValueError):
            factory.create_agent(InvalidAgentType())
    
    def test_create_agent_for_config(self, factory):
        """
        Test creating an agent from a configuration.
        """
        # Create configuration
        config = {
            "agent_type": "documentation",
            "name": "Test Agent",
            "description": "Test agent configuration"
        }
        
        # Create agent
        agent = factory.create_agent_for_config(config)
        
        # Verify agent type
        assert isinstance(agent, DocumentationAgent)
        assert agent.llm_service == factory.llm_service
        assert agent.documentation_service == factory.documentation_service
    
    def test_create_agent_for_config_enum(self, factory):
        """
        Test creating an agent from a configuration with enum agent type.
        """
        # Create configuration
        config = {
            "agent_type": AgentType.TROUBLESHOOTING,
            "name": "Test Agent",
            "description": "Test agent configuration"
        }
        
        # Create agent
        agent = factory.create_agent_for_config(config)
        
        # Verify agent type
        assert isinstance(agent, TroubleshootingAgent)
        assert agent.llm_service == factory.llm_service
        assert agent.troubleshooting_service == factory.troubleshooting_service
    
    def test_create_agent_for_config_missing_type(self, factory):
        """
        Test creating an agent from a configuration with missing agent type.
        """
        # Create configuration
        config = {
            "name": "Test Agent",
            "description": "Test agent configuration"
        }
        
        # Verify ValueError is raised
        with pytest.raises(ValueError):
            factory.create_agent_for_config(config)
    
    def test_create_agent_for_config_invalid_type(self, factory):
        """
        Test creating an agent from a configuration with invalid agent type.
        """
        # Create configuration
        config = {
            "agent_type": "invalid_type",
            "name": "Test Agent",
            "description": "Test agent configuration"
        }
        
        # Verify ValueError is raised
        with pytest.raises(ValueError):
            factory.create_agent_for_config(config)
