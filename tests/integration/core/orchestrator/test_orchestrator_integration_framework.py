"""
Integration tests for the orchestrator using the integration testing framework.

This module demonstrates the usage of the integration testing framework for testing
the orchestrator component.
"""
import pytest
import asyncio
from typing import Dict, List, Any

from app.models.conversation import AgentType
from app.models.orchestrator import OrchestratorRequest, OrchestratorResponse
from app.core.orchestrator.orchestrator import Orchestrator
from app.core.agents.factory import AgentFactory

from tests.framework.integration.environment import IntegrationTestEnvironment, DependencyType
from tests.framework.integration.harness import InteractionTracker, TrackedComponent
from tests.framework.integration.scenarios import (
    SimpleQueryScenario, MultiTurnConversationScenario, AgentSwitchingScenario
)
from tests.framework.integration.runner import TestRunner, TestSuite
from tests.framework.utilities.input_simulator import InputSimulator

# Import fixtures
pytest_plugins = ["tests.conftest_agent", "tests.conftest_orchestrator"]


class TestOrchestratorIntegration:
    """
    Integration tests for the orchestrator using the integration testing framework.
    """
    
    @pytest.fixture
    def test_environment(self):
        """
        Create integration test environment.
        
        Returns:
            IntegrationTestEnvironment: Integration test environment
        """
        # Create integration test environment
        env = IntegrationTestEnvironment()
        
        yield env
        
        # Clean up
        env.cleanup()
    
    @pytest.fixture
    def test_runner(self, test_environment):
        """
        Create test runner.
        
        Args:
            test_environment: Integration test environment
            
        Returns:
            TestRunner: Test runner
        """
        # Create test runner
        runner = TestRunner(environment=test_environment)
        
        yield runner
        
        # Clean up
        runner.cleanup()
    
    @pytest.fixture
    def orchestrator(
        self,
        mock_llm_service,
        mock_agent_repository,
        mock_conversation_repository
    ):
        """
        Create orchestrator.
        
        Args:
            mock_llm_service: Mock LLM service
            mock_agent_repository: Mock agent repository
            mock_conversation_repository: Mock conversation repository
            
        Returns:
            Orchestrator: Orchestrator
        """
        # Create orchestrator
        orchestrator = Orchestrator(
            llm_service=mock_llm_service,
            agent_repository=mock_agent_repository,
            conversation_repository=mock_conversation_repository
        )
        
        return orchestrator
    
    @pytest.fixture
    def agent_factory(
        self,
        mock_llm_service,
        mock_documentation_service,
        mock_troubleshooting_service,
        mock_maintenance_service
    ):
        """
        Create agent factory.
        
        Args:
            mock_llm_service: Mock LLM service
            mock_documentation_service: Mock documentation service
            mock_troubleshooting_service: Mock troubleshooting service
            mock_maintenance_service: Mock maintenance service
            
        Returns:
            AgentFactory: Agent factory
        """
        # Create agent factory
        factory = AgentFactory(
            llm_service=mock_llm_service,
            documentation_service=mock_documentation_service,
            troubleshooting_service=mock_troubleshooting_service,
            maintenance_service=mock_maintenance_service
        )
        
        return factory
    
    @pytest.mark.asyncio
    async def test_simple_query_scenario(self, orchestrator):
        """
        Test simple query scenario.
        
        Args:
            orchestrator: Orchestrator
        """
        # Create interaction tracker
        tracker = InteractionTracker()
        
        # Create input simulator
        input_simulator = InputSimulator()
        
        # Create simple query scenario
        scenario = SimpleQueryScenario(
            orchestrator=orchestrator,
            agent_type=AgentType.DOCUMENTATION,
            tracker=tracker,
            input_simulator=input_simulator
        )
        
        # Run scenario
        response = await scenario.run()
        
        # Verify response
        assert response is not None
        assert isinstance(response, OrchestratorResponse)
        assert response.content is not None
        
        # Verify interactions
        interactions = tracker.get_interactions()
        assert len(interactions) > 0
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation_scenario(self, orchestrator):
        """
        Test multi-turn conversation scenario.
        
        Args:
            orchestrator: Orchestrator
        """
        # Create interaction tracker
        tracker = InteractionTracker()
        
        # Create input simulator
        input_simulator = InputSimulator()
        
        # Create multi-turn conversation scenario
        scenario = MultiTurnConversationScenario(
            orchestrator=orchestrator,
            agent_type=AgentType.DOCUMENTATION,
            num_turns=2,
            tracker=tracker,
            input_simulator=input_simulator
        )
        
        # Run scenario
        responses = await scenario.run()
        
        # Verify responses
        assert responses is not None
        assert len(responses) == 2
        assert all(isinstance(response, OrchestratorResponse) for response in responses)
        
        # Verify interactions
        interactions = tracker.get_interactions()
        assert len(interactions) > 0
    
    @pytest.mark.asyncio
    async def test_agent_switching_scenario(self, orchestrator):
        """
        Test agent switching scenario.
        
        Args:
            orchestrator: Orchestrator
        """
        # Create interaction tracker
        tracker = InteractionTracker()
        
        # Create input simulator
        input_simulator = InputSimulator()
        
        # Create agent switching scenario
        scenario = AgentSwitchingScenario(
            orchestrator=orchestrator,
            agent_sequence=[
                AgentType.DOCUMENTATION,
                AgentType.TROUBLESHOOTING,
                AgentType.MAINTENANCE
            ],
            tracker=tracker,
            input_simulator=input_simulator
        )
        
        # Run scenario
        responses = await scenario.run()
        
        # Verify responses
        assert responses is not None
        assert len(responses) == 3
        assert all(isinstance(response, OrchestratorResponse) for response in responses)
        
        # Verify interactions
        interactions = tracker.get_interactions()
        assert len(interactions) > 0
    
    @pytest.mark.asyncio
    async def test_orchestrator_with_test_runner(
        self, test_runner, orchestrator
    ):
        """
        Test orchestrator with test runner.
        
        Args:
            test_runner: Test runner
            orchestrator: Orchestrator
        """
        # Create test suite
        suite = test_runner.create_suite(
            name="Orchestrator Test Suite",
            description="Test suite for orchestrator"
        )
        
        # Create interaction tracker
        tracker = InteractionTracker()
        
        # Create input simulator
        input_simulator = InputSimulator()
        
        # Add scenarios
        suite.add_scenario(SimpleQueryScenario(
            orchestrator=orchestrator,
            agent_type=AgentType.DOCUMENTATION,
            tracker=tracker,
            input_simulator=input_simulator
        ))
        
        suite.add_scenario(MultiTurnConversationScenario(
            orchestrator=orchestrator,
            agent_type=AgentType.TROUBLESHOOTING,
            num_turns=2,
            tracker=tracker,
            input_simulator=input_simulator
        ))
        
        # Run test suite
        results = await test_runner.run_suite(suite)
        
        # Verify results
        assert results is not None
        assert len(results) == 2
        assert all(result.success for result in results)
