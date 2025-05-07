"""
Agent registry for the MAGPIE platform.

This module provides functionality for registering and discovering agents
based on their capabilities and metadata.
"""
import logging
import time
from typing import Dict, List, Optional, Set, Tuple

from app.models.conversation import AgentType
from app.models.orchestrator import AgentCapability, AgentMetadata
from app.repositories.agent import AgentConfigurationRepository

# Configure logging
logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Registry for managing available agents and their capabilities.
    """

    def __init__(
        self,
        agent_repository: AgentConfigurationRepository,
        cache_ttl_seconds: int = 300  # 5 minutes cache TTL
    ):
        """
        Initialize the agent registry.

        Args:
            agent_repository: Repository for agent configurations
            cache_ttl_seconds: Time-to-live for the cache in seconds
        """
        self.agent_repository = agent_repository
        self._agent_metadata_cache: Dict[AgentType, List[AgentMetadata]] = {}
        self._capability_index: Dict[str, Set[int]] = {}  # Maps capability keywords to agent config IDs
        self._last_refresh_time: float = 0
        self._cache_ttl_seconds = cache_ttl_seconds
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize the agent registry by loading all agent configurations.
        """
        if self._initialized and not self._is_cache_expired():
            return

        try:
            # Clear existing cache
            self._agent_metadata_cache.clear()
            self._capability_index.clear()

            # Load all agent configurations
            for agent_type in AgentType:
                configs = self.agent_repository.get_by_agent_type(agent_type, active_only=True)

                if not configs:
                    logger.warning(f"No active configurations found for agent type: {agent_type}")
                    continue

                metadata_list = []
                for config in configs:
                    # Create agent metadata from configuration
                    metadata = self._create_agent_metadata(config)
                    metadata_list.append(metadata)

                    # Index capabilities for faster lookup
                    self._index_agent_capabilities(metadata)

                self._agent_metadata_cache[agent_type] = metadata_list

            # Update refresh time
            self._last_refresh_time = time.time()
            self._initialized = True
            logger.info("Agent registry initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing agent registry: {str(e)}")
            raise

    def _is_cache_expired(self) -> bool:
        """
        Check if the cache has expired.

        Returns:
            bool: True if cache has expired, False otherwise
        """
        return (time.time() - self._last_refresh_time) > self._cache_ttl_seconds

    def _create_agent_metadata(self, config) -> AgentMetadata:
        """
        Create agent metadata from configuration.

        Args:
            config: Agent configuration

        Returns:
            AgentMetadata: Agent metadata
        """
        # Extract capabilities from metadata if available
        capabilities = []
        if config.meta_data and "capabilities" in config.meta_data:
            for cap_data in config.meta_data["capabilities"]:
                capability = AgentCapability(
                    name=cap_data.get("name", "Unknown"),
                    description=cap_data.get("description", ""),
                    keywords=cap_data.get("keywords", []),
                    examples=cap_data.get("examples", [])
                )
                capabilities.append(capability)

        # If no capabilities defined, create a default one
        if not capabilities:
            if config.agent_type == AgentType.DOCUMENTATION:
                capabilities = [
                    AgentCapability(
                        name="Documentation Search",
                        description="Find and extract information from technical documentation",
                        keywords=["manual", "document", "find", "search", "information", "documentation"],
                        examples=["Where can I find information about landing gear maintenance?"]
                    )
                ]
            elif config.agent_type == AgentType.TROUBLESHOOTING:
                capabilities = [
                    AgentCapability(
                        name="Problem Diagnosis",
                        description="Diagnose issues based on symptoms and maintenance history",
                        keywords=["problem", "issue", "error", "diagnose", "troubleshoot", "fix"],
                        examples=["The hydraulic system is showing low pressure, what could be the cause?"]
                    )
                ]
            elif config.agent_type == AgentType.MAINTENANCE:
                capabilities = [
                    AgentCapability(
                        name="Procedure Generation",
                        description="Create maintenance procedures based on aircraft configuration",
                        keywords=["procedure", "steps", "maintenance", "how to", "instructions"],
                        examples=["What are the steps to replace the fuel filter on a Boeing 737?"]
                    )
                ]

        # Determine if this is the default agent for its type
        is_default = False
        if config.meta_data and config.meta_data.get("is_default"):
            is_default = True
        elif "default" in config.name.lower():
            is_default = True

        # Create and return metadata
        return AgentMetadata(
            agent_type=config.agent_type,
            name=config.name,
            description=config.description or f"{config.agent_type.value.capitalize()} Agent",
            capabilities=capabilities,
            config_id=config.id,
            is_default=is_default,
            additional_info=config.meta_data
        )

    def _index_agent_capabilities(self, agent_metadata: AgentMetadata) -> None:
        """
        Index agent capabilities for faster lookup.

        Args:
            agent_metadata: Agent metadata to index
        """
        if not agent_metadata.config_id:
            return

        # Add all capability keywords to the index
        for capability in agent_metadata.capabilities:
            for keyword in capability.keywords:
                keyword_lower = keyword.lower()
                if keyword_lower not in self._capability_index:
                    self._capability_index[keyword_lower] = set()
                self._capability_index[keyword_lower].add(agent_metadata.config_id)

    def get_all_agents(self) -> List[AgentMetadata]:
        """
        Get metadata for all registered agents.

        Returns:
            List[AgentMetadata]: List of agent metadata
        """
        if not self._initialized:
            raise RuntimeError("Agent registry not initialized. Call initialize() first.")

        # Check if cache needs refresh
        if self._is_cache_expired():
            logger.info("Agent registry cache expired, refreshing...")
            self.refresh()

        all_agents = []
        for agent_list in self._agent_metadata_cache.values():
            all_agents.extend(agent_list)

        return all_agents

    def get_agents_by_type(self, agent_type: AgentType) -> List[AgentMetadata]:
        """
        Get metadata for all agents of a specific type.

        Args:
            agent_type: Agent type

        Returns:
            List[AgentMetadata]: List of agent metadata
        """
        if not self._initialized:
            raise RuntimeError("Agent registry not initialized. Call initialize() first.")

        # Check if cache needs refresh
        if self._is_cache_expired():
            logger.info("Agent registry cache expired, refreshing...")
            self.refresh()

        return self._agent_metadata_cache.get(agent_type, [])

    def get_default_agent(self, agent_type: AgentType) -> Optional[AgentMetadata]:
        """
        Get the default agent for a specific type.

        Args:
            agent_type: Agent type

        Returns:
            Optional[AgentMetadata]: Default agent metadata or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Agent registry not initialized. Call initialize() first.")

        # Check if cache needs refresh
        if self._is_cache_expired():
            logger.info("Agent registry cache expired, refreshing...")
            self.refresh()

        agents = self.get_agents_by_type(agent_type)

        # First, look for agents explicitly marked as default
        for agent in agents:
            if agent.is_default:
                return agent

        # If no default found, return the first one if available
        return agents[0] if agents else None

    def find_agents_by_capability(self, keywords: List[str]) -> List[Tuple[AgentMetadata, int]]:
        """
        Find agents that match the given capability keywords.

        Args:
            keywords: List of capability keywords to match

        Returns:
            List[Tuple[AgentMetadata, int]]: List of (agent metadata, match count) tuples,
                                            sorted by match count in descending order
        """
        if not self._initialized:
            raise RuntimeError("Agent registry not initialized. Call initialize() first.")

        # Check if cache needs refresh
        if self._is_cache_expired():
            logger.info("Agent registry cache expired, refreshing...")
            self.refresh()

        # Find matching agent IDs and count matches
        agent_match_counts: Dict[int, int] = {}
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in self._capability_index:
                for agent_id in self._capability_index[keyword_lower]:
                    if agent_id not in agent_match_counts:
                        agent_match_counts[agent_id] = 0
                    agent_match_counts[agent_id] += 1

        # Get agent metadata for matching IDs
        results = []
        for agent_id, match_count in agent_match_counts.items():
            # Find the agent metadata for this ID
            for agent_list in self._agent_metadata_cache.values():
                for agent in agent_list:
                    if agent.config_id == agent_id:
                        results.append((agent, match_count))
                        break

        # Sort by match count in descending order
        results.sort(key=lambda x: x[1], reverse=True)

        return results

    def get_agent_by_id(self, config_id: int) -> Optional[AgentMetadata]:
        """
        Get agent metadata by configuration ID.

        Args:
            config_id: Agent configuration ID

        Returns:
            Optional[AgentMetadata]: Agent metadata or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Agent registry not initialized. Call initialize() first.")

        # Check if cache needs refresh
        if self._is_cache_expired():
            logger.info("Agent registry cache expired, refreshing...")
            self.refresh()

        # Search for the agent in all types
        for agent_list in self._agent_metadata_cache.values():
            for agent in agent_list:
                if agent.config_id == config_id:
                    return agent

        return None

    def refresh(self) -> None:
        """
        Refresh the agent registry by clearing the cache and reloading configurations.
        """
        self._agent_metadata_cache.clear()
        self._capability_index.clear()
        self._initialized = False
        self._last_refresh_time = 0
