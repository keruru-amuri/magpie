"""
Unit tests for the agent registry.
"""
import pytest
import time
from unittest.mock import MagicMock, patch

from app.core.orchestrator.registry import AgentRegistry
from app.models.conversation import AgentType
from app.models.orchestrator import AgentCapability, AgentMetadata


@pytest.fixture
def mock_agent_repository():
    """
    Create a mock agent repository.
    """
    mock_repo = MagicMock()
    
    # Mock agent configurations
    doc_config = MagicMock()
    doc_config.id = 1
    doc_config.agent_type = AgentType.DOCUMENTATION
    doc_config.name = "Documentation Assistant"
    doc_config.description = "Helps find information in technical documentation"
    doc_config.meta_data = {
        "is_default": True,
        "capabilities": [
            {
                "name": "Documentation Search",
                "description": "Find and extract information from technical documentation",
                "keywords": ["manual", "document", "find", "search", "information"],
                "examples": ["Where can I find information about landing gear maintenance?"]
            }
        ]
    }
    
    ts_config = MagicMock()
    ts_config.id = 2
    ts_config.agent_type = AgentType.TROUBLESHOOTING
    ts_config.name = "Troubleshooting Advisor"
    ts_config.description = "Helps diagnose and resolve issues"
    ts_config.meta_data = {
        "is_default": True,
        "capabilities": [
            {
                "name": "Problem Diagnosis",
                "description": "Diagnose issues based on symptoms",
                "keywords": ["problem", "issue", "error", "diagnose", "troubleshoot"],
                "examples": ["The hydraulic system is showing low pressure, what could be the cause?"]
            }
        ]
    }
    
    maint_config = MagicMock()
    maint_config.id = 3
    maint_config.agent_type = AgentType.MAINTENANCE
    maint_config.name = "Maintenance Procedure Generator"
    maint_config.description = "Creates maintenance procedures"
    maint_config.meta_data = {
        "is_default": True,
        "capabilities": [
            {
                "name": "Procedure Generation",
                "description": "Create maintenance procedures",
                "keywords": ["procedure", "steps", "maintenance", "how to"],
                "examples": ["What are the steps to replace the fuel filter?"]
            }
        ]
    }
    
    # Configure mock repository to return appropriate configurations
    mock_repo.get_by_agent_type.side_effect = lambda agent_type, active_only=True: {
        AgentType.DOCUMENTATION: [doc_config],
        AgentType.TROUBLESHOOTING: [ts_config],
        AgentType.MAINTENANCE: [maint_config]
    }.get(agent_type, [])
    
    return mock_repo


@pytest.fixture
def registry(mock_agent_repository):
    """
    Create an agent registry with a mock repository.
    """
    return AgentRegistry(mock_agent_repository, cache_ttl_seconds=1)  # Short TTL for testing


class TestAgentRegistry:
    """
    Tests for the AgentRegistry class.
    """

    @pytest.mark.asyncio
    async def test_initialize(self, registry):
        """
        Test initializing the registry.
        """
        # Initialize the registry
        await registry.initialize()
        
        # Verify registry is initialized
        assert registry._initialized is True
        assert len(registry._agent_metadata_cache) > 0
        assert len(registry._capability_index) > 0

    @pytest.mark.asyncio
    async def test_get_all_agents(self, registry):
        """
        Test getting all agents.
        """
        # Initialize the registry
        await registry.initialize()
        
        # Get all agents
        agents = registry.get_all_agents()
        
        # Verify result
        assert len(agents) == 3  # One agent for each type
        assert any(agent.agent_type == AgentType.DOCUMENTATION for agent in agents)
        assert any(agent.agent_type == AgentType.TROUBLESHOOTING for agent in agents)
        assert any(agent.agent_type == AgentType.MAINTENANCE for agent in agents)

    @pytest.mark.asyncio
    async def test_get_agents_by_type(self, registry):
        """
        Test getting agents by type.
        """
        # Initialize the registry
        await registry.initialize()
        
        # Get agents by type
        doc_agents = registry.get_agents_by_type(AgentType.DOCUMENTATION)
        ts_agents = registry.get_agents_by_type(AgentType.TROUBLESHOOTING)
        maint_agents = registry.get_agents_by_type(AgentType.MAINTENANCE)
        
        # Verify results
        assert len(doc_agents) == 1
        assert doc_agents[0].agent_type == AgentType.DOCUMENTATION
        
        assert len(ts_agents) == 1
        assert ts_agents[0].agent_type == AgentType.TROUBLESHOOTING
        
        assert len(maint_agents) == 1
        assert maint_agents[0].agent_type == AgentType.MAINTENANCE

    @pytest.mark.asyncio
    async def test_get_default_agent(self, registry):
        """
        Test getting the default agent for a type.
        """
        # Initialize the registry
        await registry.initialize()
        
        # Get default agents
        doc_agent = registry.get_default_agent(AgentType.DOCUMENTATION)
        ts_agent = registry.get_default_agent(AgentType.TROUBLESHOOTING)
        maint_agent = registry.get_default_agent(AgentType.MAINTENANCE)
        
        # Verify results
        assert doc_agent is not None
        assert doc_agent.agent_type == AgentType.DOCUMENTATION
        assert doc_agent.is_default is True
        
        assert ts_agent is not None
        assert ts_agent.agent_type == AgentType.TROUBLESHOOTING
        assert ts_agent.is_default is True
        
        assert maint_agent is not None
        assert maint_agent.agent_type == AgentType.MAINTENANCE
        assert maint_agent.is_default is True

    @pytest.mark.asyncio
    async def test_find_agents_by_capability(self, registry):
        """
        Test finding agents by capability keywords.
        """
        # Initialize the registry
        await registry.initialize()
        
        # Find agents by capability
        doc_keywords = ["document", "manual", "find"]
        doc_matches = registry.find_agents_by_capability(doc_keywords)
        
        ts_keywords = ["problem", "issue", "troubleshoot"]
        ts_matches = registry.find_agents_by_capability(ts_keywords)
        
        maint_keywords = ["procedure", "steps", "maintenance"]
        maint_matches = registry.find_agents_by_capability(maint_keywords)
        
        # Verify results
        assert len(doc_matches) > 0
        assert doc_matches[0][0].agent_type == AgentType.DOCUMENTATION
        assert doc_matches[0][1] > 0  # Match count
        
        assert len(ts_matches) > 0
        assert ts_matches[0][0].agent_type == AgentType.TROUBLESHOOTING
        assert ts_matches[0][1] > 0  # Match count
        
        assert len(maint_matches) > 0
        assert maint_matches[0][0].agent_type == AgentType.MAINTENANCE
        assert maint_matches[0][1] > 0  # Match count

    @pytest.mark.asyncio
    async def test_get_agent_by_id(self, registry):
        """
        Test getting an agent by ID.
        """
        # Initialize the registry
        await registry.initialize()
        
        # Get agent by ID
        agent = registry.get_agent_by_id(1)  # Documentation agent
        
        # Verify result
        assert agent is not None
        assert agent.agent_type == AgentType.DOCUMENTATION
        assert agent.config_id == 1

    @pytest.mark.asyncio
    async def test_cache_expiration(self, registry):
        """
        Test cache expiration.
        """
        # Initialize the registry
        await registry.initialize()
        
        # Verify cache is not expired
        assert registry._is_cache_expired() is False
        
        # Wait for cache to expire (TTL is 1 second)
        time.sleep(1.1)
        
        # Verify cache is expired
        assert registry._is_cache_expired() is True
        
        # Mock the initialize method to verify it's called on cache expiration
        registry.initialize = MagicMock()
        
        # Get all agents (should trigger cache refresh)
        registry.get_all_agents()
        
        # Verify initialize was called
        registry.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh(self, registry):
        """
        Test refreshing the registry.
        """
        # Initialize the registry
        await registry.initialize()
        
        # Verify registry is initialized
        assert registry._initialized is True
        
        # Refresh the registry
        registry.refresh()
        
        # Verify registry is no longer initialized
        assert registry._initialized is False
        assert len(registry._agent_metadata_cache) == 0
        assert len(registry._capability_index) == 0
