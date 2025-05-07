"""
Agent repository for the MAGPIE platform.
"""
import logging
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.agent import AgentConfiguration, ModelSize
from app.models.conversation import AgentType
from app.repositories.base import BaseRepository

# Configure logging
logger = logging.getLogger(__name__)


class AgentConfigurationRepository(BaseRepository[AgentConfiguration]):
    """
    Repository for AgentConfiguration model.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(AgentConfiguration, session)

    def get_by_name(self, name: str) -> Optional[AgentConfiguration]:
        """
        Get agent configuration by name.

        Args:
            name: Agent configuration name

        Returns:
            Optional[AgentConfiguration]: Agent configuration or None if not found
        """
        try:
            query = select(AgentConfiguration).where(AgentConfiguration.name == name)
            result = self.session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting agent configuration by name: {str(e)}")
            return None

    def get_by_agent_type(
        self,
        agent_type: AgentType,
        active_only: bool = True
    ) -> List[AgentConfiguration]:
        """
        Get agent configurations by agent type.

        Args:
            agent_type: Agent type
            active_only: Only return active configurations

        Returns:
            List[AgentConfiguration]: List of agent configurations
        """
        try:
            query = select(AgentConfiguration).where(AgentConfiguration.agent_type == agent_type)

            if active_only:
                query = query.where(AgentConfiguration.is_active == True)

            result = self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting agent configurations by agent type: {str(e)}")
            return []

    def get_by_model_size(
        self,
        model_size: ModelSize,
        active_only: bool = True
    ) -> List[AgentConfiguration]:
        """
        Get agent configurations by model size.

        Args:
            model_size: Model size
            active_only: Only return active configurations

        Returns:
            List[AgentConfiguration]: List of agent configurations
        """
        try:
            query = select(AgentConfiguration).where(AgentConfiguration.model_size == model_size)

            if active_only:
                query = query.where(AgentConfiguration.is_active == True)

            result = self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting agent configurations by model size: {str(e)}")
            return []

    def get_default_configuration(
        self,
        agent_type: AgentType
    ) -> Optional[AgentConfiguration]:
        """
        Get default agent configuration for agent type.

        Args:
            agent_type: Agent type

        Returns:
            Optional[AgentConfiguration]: Default agent configuration or None if not found
        """
        try:
            # Get active configurations for agent type
            configurations = self.get_by_agent_type(agent_type, active_only=True)

            if not configurations:
                return None

            # Find configuration with "default" in name or meta_data
            for config in configurations:
                if "default" in config.name.lower():
                    return config

                if config.meta_data and config.meta_data.get("is_default"):
                    return config

            # If no default found, return first active configuration
            return configurations[0]
        except Exception as e:
            logger.error(f"Error getting default agent configuration: {str(e)}")
            return None

    def update_system_prompt(
        self,
        config_id: int,
        system_prompt: str
    ) -> bool:
        """
        Update system prompt for agent configuration.

        Args:
            config_id: Agent configuration ID
            system_prompt: New system prompt

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            config = self.get_by_id(config_id)
            if not config:
                return False

            config.system_prompt = system_prompt
            self.session.flush()

            # Update cache
            self._cache_set(config)

            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating system prompt: {str(e)}")
            return False

    def update_model_parameters(
        self,
        config_id: int,
        model_size: Optional[ModelSize] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> bool:
        """
        Update model parameters for agent configuration.

        Args:
            config_id: Agent configuration ID
            model_size: New model size
            temperature: New temperature
            max_tokens: New max tokens

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            config = self.get_by_id(config_id)
            if not config:
                return False

            if model_size is not None:
                config.model_size = model_size

            if temperature is not None:
                config.temperature = temperature

            if max_tokens is not None:
                config.max_tokens = max_tokens

            self.session.flush()

            # Update cache
            self._cache_set(config)

            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating model parameters: {str(e)}")
            return False

    def update_metadata(
        self,
        config_id: int,
        metadata: Dict
    ) -> bool:
        """
        Update metadata for agent configuration.

        Args:
            config_id: Agent configuration ID
            metadata: New metadata

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            config = self.get_by_id(config_id)
            if not config:
                return False

            # Merge with existing meta_data if any
            if config.meta_data:
                config.meta_data.update(metadata)
            else:
                config.meta_data = metadata

            self.session.flush()

            # Update cache
            self._cache_set(config)

            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating metadata: {str(e)}")
            return False
