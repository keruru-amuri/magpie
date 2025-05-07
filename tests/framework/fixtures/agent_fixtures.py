"""
Test fixtures for agent testing.

This module provides fixtures for testing agent components and system functionality.
"""
import pytest
import asyncio
import uuid
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import MagicMock, AsyncMock

from app.models.conversation import AgentType, MessageRole
from app.models.agent import AgentConfiguration, ModelSize
from app.core.agents.documentation_agent import DocumentationAgent
from app.core.agents.troubleshooting_agent import TroubleshootingAgent
from app.core.agents.maintenance_agent import MaintenanceAgent
from app.services.llm_service import LLMService
from app.core.mock.service import MockDataService

from tests.framework.utilities.input_simulator import InputSimulator


class MockLLMService:
    """Mock LLM service for testing."""
    
    def __init__(self, response_template: Optional[str] = None):
        """
        Initialize the mock LLM service.
        
        Args:
            response_template: Optional response template
        """
        self.response_template = response_template or "This is a mock response for: {query}"
        self.call_history = []
    
    async def generate_response_async(
        self, messages: List[Dict[str, str]], model_size: ModelSize = ModelSize.MEDIUM,
        temperature: float = 0.7, max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate a mock response.
        
        Args:
            messages: List of messages
            model_size: Model size
            temperature: Temperature
            max_tokens: Maximum tokens
            
        Returns:
            Mock response
        """
        # Record call
        self.call_history.append({
            "messages": messages,
            "model_size": model_size,
            "temperature": temperature,
            "max_tokens": max_tokens
        })
        
        # Extract query from last user message
        query = "unknown query"
        for message in reversed(messages):
            if message["role"] == "user":
                query = message["content"]
                break
        
        # Generate response
        response = {
            "content": self.response_template.format(query=query),
            "model": f"gpt-4.1-{model_size.value}",
            "usage": {
                "prompt_tokens": sum(len(m["content"].split()) for m in messages),
                "completion_tokens": 50,
                "total_tokens": sum(len(m["content"].split()) for m in messages) + 50
            }
        }
        
        return response
    
    async def generate_custom_response_async(
        self, messages: List[Dict[str, str]], model_size: ModelSize = ModelSize.MEDIUM,
        temperature: float = 0.7, max_tokens: int = 1000, **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a mock custom response.
        
        Args:
            messages: List of messages
            model_size: Model size
            temperature: Temperature
            max_tokens: Maximum tokens
            **kwargs: Additional arguments
            
        Returns:
            Mock response
        """
        return await self.generate_response_async(
            messages, model_size, temperature, max_tokens
        )
    
    async def analyze_complexity_async(
        self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze query complexity.
        
        Args:
            query: Query to analyze
            conversation_history: Optional conversation history
            
        Returns:
            Mock complexity analysis
        """
        # Record call
        self.call_history.append({
            "method": "analyze_complexity_async",
            "query": query,
            "conversation_history": conversation_history
        })
        
        # Simple complexity analysis based on query length
        query_length = len(query.split())
        if query_length < 10:
            complexity = "low"
            score = 3.0
        elif query_length < 20:
            complexity = "medium"
            score = 6.0
        else:
            complexity = "high"
            score = 9.0
        
        return {
            "complexity": complexity,
            "score": score,
            "dimensions": {
                "length": min(10, query_length / 5),
                "technical_terms": min(10, query_length / 10),
                "context_dependency": min(10, query_length / 15)
            },
            "reasoning": f"Query has {query_length} words, indicating {complexity} complexity."
        }


class MockDocumentationService:
    """Mock documentation service for testing."""
    
    def __init__(self, mock_data: Optional[Dict[str, Any]] = None):
        """
        Initialize the mock documentation service.
        
        Args:
            mock_data: Optional mock data
        """
        self.mock_data = mock_data or {}
        self.call_history = []
    
    async def search_documentation(
        self, query: str, limit: int = 5, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search documentation.
        
        Args:
            query: Search query
            limit: Result limit
            **kwargs: Additional arguments
            
        Returns:
            Mock search results
        """
        # Record call
        self.call_history.append({
            "method": "search_documentation",
            "query": query,
            "limit": limit,
            "kwargs": kwargs
        })
        
        # Return mock results
        results = self.mock_data.get("search_results", [])
        if not results:
            # Generate mock results if none provided
            results = [
                {
                    "id": f"doc-{i+1:03d}",
                    "title": f"Mock Document {i+1}",
                    "content": f"This is mock content for document {i+1} related to {query}",
                    "relevance": 0.9 - (i * 0.1),
                    "source": "Mock Source",
                    "document_type": ["manual", "bulletin", "directive"][i % 3]
                }
                for i in range(min(limit, 5))
            ]
        
        return results[:limit]
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Mock document
        """
        # Record call
        self.call_history.append({
            "method": "get_document",
            "document_id": document_id
        })
        
        # Return mock document
        documents = self.mock_data.get("documents", {})
        if document_id in documents:
            return documents[document_id]
        
        # Generate mock document if not found
        return {
            "id": document_id,
            "title": f"Mock Document {document_id}",
            "content": f"This is mock content for document {document_id}",
            "source": "Mock Source",
            "document_type": "manual",
            "metadata": {
                "aircraft_type": "Boeing 737",
                "system": "Hydraulic",
                "revision": "Rev A",
                "date": "2023-01-15"
            }
        }


class MockTroubleshootingService:
    """Mock troubleshooting service for testing."""
    
    def __init__(self, mock_data: Optional[Dict[str, Any]] = None):
        """
        Initialize the mock troubleshooting service.
        
        Args:
            mock_data: Optional mock data
        """
        self.mock_data = mock_data or {}
        self.call_history = []
    
    async def search_troubleshooting_cases(
        self, query: str, limit: int = 5, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search troubleshooting cases.
        
        Args:
            query: Search query
            limit: Result limit
            **kwargs: Additional arguments
            
        Returns:
            Mock search results
        """
        # Record call
        self.call_history.append({
            "method": "search_troubleshooting_cases",
            "query": query,
            "limit": limit,
            "kwargs": kwargs
        })
        
        # Return mock results
        results = self.mock_data.get("search_results", [])
        if not results:
            # Generate mock results if none provided
            results = [
                {
                    "id": f"case-{i+1:03d}",
                    "title": f"Mock Troubleshooting Case {i+1}",
                    "symptoms": [f"Symptom {j+1}" for j in range(2)],
                    "system": ["Hydraulic", "Electrical", "Avionics"][i % 3],
                    "relevance": 0.9 - (i * 0.1),
                    "resolution": f"This is a mock resolution for case {i+1}"
                }
                for i in range(min(limit, 5))
            ]
        
        return results[:limit]
    
    async def get_troubleshooting_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Get troubleshooting case by ID.
        
        Args:
            case_id: Case ID
            
        Returns:
            Mock case
        """
        # Record call
        self.call_history.append({
            "method": "get_troubleshooting_case",
            "case_id": case_id
        })
        
        # Return mock case
        cases = self.mock_data.get("cases", {})
        if case_id in cases:
            return cases[case_id]
        
        # Generate mock case if not found
        return {
            "id": case_id,
            "title": f"Mock Troubleshooting Case {case_id}",
            "symptoms": ["Warning Light", "Unusual Noise"],
            "system": "Hydraulic",
            "aircraft_type": "Boeing 737",
            "diagnosis": {
                "potential_causes": [
                    {
                        "id": "cause-001",
                        "description": "Faulty component",
                        "probability": 0.75
                    },
                    {
                        "id": "cause-002",
                        "description": "Loose connection",
                        "probability": 0.25
                    }
                ],
                "recommended_actions": [
                    {
                        "id": "action-001",
                        "description": "Inspect component",
                        "priority": "high"
                    },
                    {
                        "id": "action-002",
                        "description": "Check connections",
                        "priority": "medium"
                    }
                ]
            },
            "resolution": "This is a mock resolution for the case"
        }


class MockMaintenanceService:
    """Mock maintenance service for testing."""
    
    def __init__(self, mock_data: Optional[Dict[str, Any]] = None):
        """
        Initialize the mock maintenance service.
        
        Args:
            mock_data: Optional mock data
        """
        self.mock_data = mock_data or {}
        self.call_history = []
    
    async def generate_maintenance_procedure(
        self, aircraft_type: str, system: str, procedure_type: str,
        parameters: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Generate maintenance procedure.
        
        Args:
            aircraft_type: Aircraft type
            system: System
            procedure_type: Procedure type
            parameters: Optional parameters
            **kwargs: Additional arguments
            
        Returns:
            Mock procedure
        """
        # Record call
        self.call_history.append({
            "method": "generate_maintenance_procedure",
            "aircraft_type": aircraft_type,
            "system": system,
            "procedure_type": procedure_type,
            "parameters": parameters,
            "kwargs": kwargs
        })
        
        # Return mock procedure
        procedures = self.mock_data.get("procedures", {})
        key = f"{aircraft_type}_{system}_{procedure_type}"
        if key in procedures:
            return procedures[key]
        
        # Generate mock procedure if not found
        return {
            "id": str(uuid.uuid4()),
            "title": f"{procedure_type} Procedure for {system} System on {aircraft_type}",
            "aircraft_type": aircraft_type,
            "system": system,
            "procedure_type": procedure_type,
            "steps": [
                {
                    "step_number": 1,
                    "description": "Prepare necessary tools and equipment",
                    "details": "Gather all required tools and equipment for the procedure"
                },
                {
                    "step_number": 2,
                    "description": f"Access the {system} system",
                    "details": f"Open access panels to reach the {system} system components"
                },
                {
                    "step_number": 3,
                    "description": f"Perform {procedure_type.lower()} on {system} system",
                    "details": f"Carefully {procedure_type.lower()} the {system} system according to specifications"
                },
                {
                    "step_number": 4,
                    "description": "Verify proper operation",
                    "details": "Test the system to ensure proper operation after maintenance"
                },
                {
                    "step_number": 5,
                    "description": "Close access panels",
                    "details": "Secure all access panels and verify proper closure"
                }
            ],
            "tools_required": ["Tool 1", "Tool 2", "Tool 3"],
            "safety_precautions": [
                "Ensure aircraft power is off",
                "Use proper personal protective equipment",
                "Follow all safety protocols"
            ],
            "estimated_time": "2 hours",
            "skill_level": "Technician",
            "references": [
                {
                    "document_id": "doc-001",
                    "title": f"{aircraft_type} Maintenance Manual",
                    "section": f"{system} System"
                }
            ]
        }
    
    async def get_maintenance_procedure_template(
        self, aircraft_type: str, system: str, procedure_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get maintenance procedure template.
        
        Args:
            aircraft_type: Aircraft type
            system: System
            procedure_type: Procedure type
            
        Returns:
            Mock template
        """
        # Record call
        self.call_history.append({
            "method": "get_maintenance_procedure_template",
            "aircraft_type": aircraft_type,
            "system": system,
            "procedure_type": procedure_type
        })
        
        # Return mock template
        templates = self.mock_data.get("templates", {})
        key = f"{aircraft_type}_{system}_{procedure_type}"
        if key in templates:
            return templates[key]
        
        # Generate mock template if not found
        return {
            "id": str(uuid.uuid4()),
            "title": f"{procedure_type} Template for {system} System on {aircraft_type}",
            "aircraft_type": aircraft_type,
            "system": system,
            "procedure_type": procedure_type,
            "template_sections": [
                {
                    "section_name": "Introduction",
                    "content": f"This procedure covers {procedure_type.lower()} of the {system} system on {aircraft_type} aircraft."
                },
                {
                    "section_name": "Safety Precautions",
                    "content": "List of safety precautions to follow during the procedure."
                },
                {
                    "section_name": "Tools and Equipment",
                    "content": "List of tools and equipment required for the procedure."
                },
                {
                    "section_name": "Procedure Steps",
                    "content": "Step-by-step instructions for performing the procedure."
                },
                {
                    "section_name": "Verification",
                    "content": "Steps to verify proper completion of the procedure."
                },
                {
                    "section_name": "Documentation",
                    "content": "Documentation requirements for the procedure."
                }
            ]
        }


@pytest.fixture
def input_simulator():
    """
    Create an input simulator.
    
    Returns:
        InputSimulator: Input simulator
    """
    return InputSimulator(seed=42)


@pytest.fixture
def mock_llm_service():
    """
    Create a mock LLM service.
    
    Returns:
        MockLLMService: Mock LLM service
    """
    return MockLLMService()


@pytest.fixture
def mock_documentation_service():
    """
    Create a mock documentation service.
    
    Returns:
        MockDocumentationService: Mock documentation service
    """
    return MockDocumentationService()


@pytest.fixture
def mock_troubleshooting_service():
    """
    Create a mock troubleshooting service.
    
    Returns:
        MockTroubleshootingService: Mock troubleshooting service
    """
    return MockTroubleshootingService()


@pytest.fixture
def mock_maintenance_service():
    """
    Create a mock maintenance service.
    
    Returns:
        MockMaintenanceService: Mock maintenance service
    """
    return MockMaintenanceService()


@pytest.fixture
def documentation_agent(mock_llm_service, mock_documentation_service):
    """
    Create a documentation agent with mock services.
    
    Args:
        mock_llm_service: Mock LLM service
        mock_documentation_service: Mock documentation service
        
    Returns:
        DocumentationAgent: Documentation agent
    """
    return DocumentationAgent(
        llm_service=mock_llm_service,
        documentation_service=mock_documentation_service
    )


@pytest.fixture
def troubleshooting_agent(mock_llm_service, mock_troubleshooting_service):
    """
    Create a troubleshooting agent with mock services.
    
    Args:
        mock_llm_service: Mock LLM service
        mock_troubleshooting_service: Mock troubleshooting service
        
    Returns:
        TroubleshootingAgent: Troubleshooting agent
    """
    return TroubleshootingAgent(
        llm_service=mock_llm_service,
        troubleshooting_service=mock_troubleshooting_service
    )


@pytest.fixture
def maintenance_agent(mock_llm_service, mock_maintenance_service):
    """
    Create a maintenance agent with mock services.
    
    Args:
        mock_llm_service: Mock LLM service
        mock_maintenance_service: Mock maintenance service
        
    Returns:
        MaintenanceAgent: Maintenance agent
    """
    return MaintenanceAgent(
        llm_service=mock_llm_service,
        maintenance_service=mock_maintenance_service
    )


@pytest.fixture
def agent_config_factory():
    """
    Factory for creating agent configurations.
    
    Returns:
        Function: Factory function
    """
    def _create_config(
        agent_type: AgentType,
        model_size: ModelSize = ModelSize.MEDIUM,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ):
        """
        Create an agent configuration.
        
        Args:
            agent_type: Agent type
            model_size: Model size
            temperature: Temperature
            max_tokens: Maximum tokens
            
        Returns:
            AgentConfiguration: Agent configuration
        """
        return AgentConfiguration(
            id=random.randint(1, 1000),
            name=f"Test {agent_type.value} Agent",
            description=f"Test {agent_type.value} agent configuration",
            agent_type=agent_type,
            model_size=model_size,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=f"You are a helpful {agent_type.value} assistant."
        )
    
    return _create_config


# Example usage
if __name__ == "__main__":
    # Create mock services
    llm_service = MockLLMService()
    documentation_service = MockDocumentationService()
    
    # Create agent
    agent = DocumentationAgent(
        llm_service=llm_service,
        documentation_service=documentation_service
    )
    
    # Test agent
    async def test_agent():
        response = await agent.process_query(
            query="What is the recommended tire pressure for a Boeing 737?",
            conversation_id=str(uuid.uuid4())
        )
        print(f"Response: {response}")
    
    # Run test
    asyncio.run(test_agent())
