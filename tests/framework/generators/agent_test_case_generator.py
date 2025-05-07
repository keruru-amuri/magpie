"""
Test case generator for agent scenarios.

This module provides a configurable test case generator for creating
varied agent test scenarios based on different parameters.
"""
import random
import uuid
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from app.models.conversation import AgentType, MessageRole
from app.models.agent import ModelSize
from app.models.complexity import ComplexityLevel


class QueryComplexity(Enum):
    """Enum for query complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class QueryType(Enum):
    """Enum for query types."""
    FACTUAL = "factual"
    PROCEDURAL = "procedural"
    DIAGNOSTIC = "diagnostic"
    COMPARATIVE = "comparative"
    HYPOTHETICAL = "hypothetical"


class AgentTestCaseGenerator:
    """
    Generator for agent test cases.
    
    This class provides methods for generating test cases for different agent scenarios.
    """
    
    # Sample queries for different agent types and complexity levels
    DOCUMENTATION_QUERIES = {
        QueryComplexity.SIMPLE: [
            "What is the recommended tire pressure for a Boeing 737?",
            "Where can I find the maintenance manual for the landing gear?",
            "What are the dimensions of the cargo bay?",
            "What is the maximum takeoff weight for an Airbus A320?",
            "How often should the oil be changed in the APU?"
        ],
        QueryComplexity.MODERATE: [
            "Compare the maintenance procedures for hydraulic systems in Boeing 737 and Airbus A320.",
            "What are the key differences between the electrical systems in the 737-800 and 737-900?",
            "Explain the troubleshooting process for a faulty fuel gauge in a Boeing 777.",
            "What are the regulatory requirements for maintaining the oxygen system?",
            "How do the maintenance intervals change for aircraft operating in humid vs. dry climates?"
        ],
        QueryComplexity.COMPLEX: [
            "Analyze the impact of the latest FAA directive on maintenance procedures for composite materials in modern aircraft.",
            "Compare and contrast the maintenance requirements for fly-by-wire systems across different aircraft manufacturers.",
            "What are the implications of the new EASA regulations on engine maintenance schedules for long-haul aircraft?",
            "Explain how the maintenance procedures for avionics systems have evolved from analog to digital systems.",
            "What are the maintenance considerations when integrating new satellite communication systems with existing avionics?"
        ]
    }
    
    TROUBLESHOOTING_QUERIES = {
        QueryComplexity.SIMPLE: [
            "The cabin pressure warning light is on. What should I check first?",
            "The APU won't start. What are the common causes?",
            "There's a hydraulic fluid leak near the landing gear. How do I diagnose it?",
            "The navigation display is flickering. What could be causing this?",
            "The engine oil pressure is reading low. What are the possible issues?"
        ],
        QueryComplexity.MODERATE: [
            "The aircraft is experiencing intermittent electrical failures during cruise. What diagnostic steps should I take?",
            "There's unusual vibration in the number 2 engine during climb. How should I troubleshoot this?",
            "The fuel quantity indicators are showing inconsistent readings. What systems should I check?",
            "The autopilot disconnects randomly during approach. What could be causing this and how do I diagnose it?",
            "The environmental control system is not maintaining proper cabin temperature. What are the possible failure points?"
        ],
        QueryComplexity.COMPLEX: [
            "We're experiencing multiple avionics failures that seem to be related to the power distribution system. How do I isolate the root cause?",
            "The aircraft has had three hydraulic system failures in the past month, but each time different components were affected. How do I approach this systemic issue?",
            "We're seeing correlated warnings across the flight control, electrical, and hydraulic systems during specific flight phases. What diagnostic approach would you recommend?",
            "The aircraft is experiencing unexplained fuel imbalance issues that don't correspond to any known failure patterns. How should I approach this investigation?",
            "We've replaced multiple components in the landing gear system but still experience intermittent extension failures. What comprehensive diagnostic approach would you recommend?"
        ]
    }
    
    MAINTENANCE_QUERIES = {
        QueryComplexity.SIMPLE: [
            "Generate a procedure for changing the oil in the APU.",
            "What's the procedure for replacing a tire on the main landing gear?",
            "Create a checklist for inspecting the cabin emergency equipment.",
            "What's the procedure for checking and replenishing hydraulic fluid?",
            "Generate a procedure for testing the emergency lighting system."
        ],
        QueryComplexity.MODERATE: [
            "Create a maintenance procedure for replacing a fuel pump that includes all safety precautions and testing requirements.",
            "Generate a detailed inspection procedure for the flight control surfaces following a lightning strike.",
            "What's the complete procedure for troubleshooting and replacing components in the cabin pressurization system?",
            "Create a maintenance procedure for overhauling the nose landing gear, including all required tooling and testing.",
            "Generate a procedure for inspecting and servicing the oxygen generation system."
        ],
        QueryComplexity.COMPLEX: [
            "Create a comprehensive maintenance procedure for replacing a section of the wing leading edge that includes structural integrity tests and aerodynamic considerations.",
            "Generate a detailed procedure for upgrading the avionics suite that includes compatibility testing with existing systems and regulatory compliance verification.",
            "What's the complete procedure for performing a major overhaul of the hydraulic system, including flushing, component replacement, and system testing?",
            "Create a maintenance procedure for addressing composite material damage that includes inspection techniques, repair methods, and structural integrity validation.",
            "Generate a procedure for implementing a service bulletin that requires modifications to multiple aircraft systems with minimal downtime."
        ]
    }
    
    # Sample expected responses for different agent types and complexity levels
    EXPECTED_RESPONSE_PATTERNS = {
        AgentType.DOCUMENTATION: {
            QueryComplexity.SIMPLE: [
                "should contain factual information",
                "should reference specific documentation",
                "should provide direct answers",
                "should include relevant specifications",
                "should cite sources"
            ],
            QueryComplexity.MODERATE: [
                "should provide comparative analysis",
                "should explain procedures",
                "should reference multiple documents",
                "should include technical details",
                "should explain regulatory context"
            ],
            QueryComplexity.COMPLEX: [
                "should provide in-depth analysis",
                "should reference multiple sources",
                "should explain complex relationships",
                "should discuss implications",
                "should provide historical context"
            ]
        },
        AgentType.TROUBLESHOOTING: {
            QueryComplexity.SIMPLE: [
                "should identify common causes",
                "should suggest initial checks",
                "should provide a diagnostic sequence",
                "should mention safety precautions",
                "should reference troubleshooting guides"
            ],
            QueryComplexity.MODERATE: [
                "should provide a systematic diagnostic approach",
                "should identify multiple potential causes",
                "should suggest test procedures",
                "should mention related systems",
                "should include verification steps"
            ],
            QueryComplexity.COMPLEX: [
                "should address systemic issues",
                "should provide a comprehensive diagnostic strategy",
                "should discuss interaction between systems",
                "should suggest root cause analysis methods",
                "should include data collection and analysis steps"
            ]
        },
        AgentType.MAINTENANCE: {
            QueryComplexity.SIMPLE: [
                "should include step-by-step instructions",
                "should list required tools",
                "should mention safety precautions",
                "should include verification steps",
                "should reference maintenance manuals"
            ],
            QueryComplexity.MODERATE: [
                "should include detailed procedures",
                "should list specialized tools and equipment",
                "should include testing procedures",
                "should mention regulatory requirements",
                "should include documentation steps"
            ],
            QueryComplexity.COMPLEX: [
                "should provide comprehensive procedures",
                "should address system interactions",
                "should include specialized testing",
                "should address regulatory compliance",
                "should include quality assurance steps"
            ]
        }
    }
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the test case generator.
        
        Args:
            seed: Optional random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
    
    def generate_test_case(
        self,
        agent_type: AgentType,
        complexity: Optional[QueryComplexity] = None,
        query_type: Optional[QueryType] = None,
        include_conversation_history: bool = False,
        conversation_turns: Optional[int] = None,
        include_context: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a test case for the specified agent type and parameters.
        
        Args:
            agent_type: Type of agent to generate test case for
            complexity: Optional complexity level (random if not specified)
            query_type: Optional query type (random if not specified)
            include_conversation_history: Whether to include conversation history
            conversation_turns: Number of conversation turns (random 1-5 if not specified)
            include_context: Whether to include additional context
            
        Returns:
            Dict containing the test case
        """
        # Select complexity if not specified
        if complexity is None:
            complexity = random.choice(list(QueryComplexity))
        
        # Select query type if not specified
        if query_type is None:
            query_type = random.choice(list(QueryType))
        
        # Select query based on agent type and complexity
        query = self._select_query(agent_type, complexity)
        
        # Generate conversation history if requested
        conversation_history = None
        if include_conversation_history:
            if conversation_turns is None:
                conversation_turns = random.randint(1, 5)
            conversation_history = self._generate_conversation_history(
                agent_type, conversation_turns
            )
        
        # Generate context if requested
        context = None
        if include_context:
            context = self._generate_context(agent_type)
        
        # Generate expected response patterns
        expected_response_patterns = self._get_expected_response_patterns(
            agent_type, complexity
        )
        
        # Create test case
        test_case = {
            "id": str(uuid.uuid4()),
            "agent_type": agent_type,
            "complexity": complexity,
            "query_type": query_type,
            "query": query,
            "expected_response_patterns": expected_response_patterns,
            "conversation_history": conversation_history,
            "context": context,
            "metadata": {
                "generated_at": str(uuid.uuid4()),
                "generator_version": "1.0.0"
            }
        }
        
        return test_case
    
    def generate_test_cases(
        self,
        count: int,
        agent_types: Optional[List[AgentType]] = None,
        complexities: Optional[List[QueryComplexity]] = None,
        query_types: Optional[List[QueryType]] = None,
        include_conversation_history_probability: float = 0.5,
        include_context_probability: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple test cases.
        
        Args:
            count: Number of test cases to generate
            agent_types: Optional list of agent types to include (all if not specified)
            complexities: Optional list of complexity levels to include (all if not specified)
            query_types: Optional list of query types to include (all if not specified)
            include_conversation_history_probability: Probability of including conversation history
            include_context_probability: Probability of including context
            
        Returns:
            List of test cases
        """
        # Use all agent types if not specified
        if agent_types is None:
            agent_types = list(AgentType)
        
        # Use all complexity levels if not specified
        if complexities is None:
            complexities = list(QueryComplexity)
        
        # Use all query types if not specified
        if query_types is None:
            query_types = list(QueryType)
        
        # Generate test cases
        test_cases = []
        for _ in range(count):
            # Select random agent type, complexity, and query type
            agent_type = random.choice(agent_types)
            complexity = random.choice(complexities)
            query_type = random.choice(query_types)
            
            # Determine whether to include conversation history and context
            include_conversation_history = random.random() < include_conversation_history_probability
            include_context = random.random() < include_context_probability
            
            # Generate test case
            test_case = self.generate_test_case(
                agent_type=agent_type,
                complexity=complexity,
                query_type=query_type,
                include_conversation_history=include_conversation_history,
                include_context=include_context
            )
            
            test_cases.append(test_case)
        
        return test_cases
    
    def _select_query(self, agent_type: AgentType, complexity: QueryComplexity) -> str:
        """
        Select a query for the specified agent type and complexity.
        
        Args:
            agent_type: Agent type
            complexity: Query complexity
            
        Returns:
            Selected query
        """
        # Select query source based on agent type
        if agent_type == AgentType.DOCUMENTATION:
            queries = self.DOCUMENTATION_QUERIES[complexity]
        elif agent_type == AgentType.TROUBLESHOOTING:
            queries = self.TROUBLESHOOTING_QUERIES[complexity]
        elif agent_type == AgentType.MAINTENANCE:
            queries = self.MAINTENANCE_QUERIES[complexity]
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")
        
        # Select random query
        return random.choice(queries)
    
    def _generate_conversation_history(
        self, agent_type: AgentType, turns: int
    ) -> List[Dict[str, str]]:
        """
        Generate conversation history.
        
        Args:
            agent_type: Agent type
            turns: Number of conversation turns
            
        Returns:
            List of conversation messages
        """
        # Generate conversation history
        conversation_history = []
        
        # Add system message
        conversation_history.append({
            "role": MessageRole.SYSTEM.value,
            "content": f"You are a helpful {agent_type.value} assistant."
        })
        
        # Add user and assistant messages
        for i in range(turns):
            # Add user message
            user_query = self._select_query(
                agent_type, random.choice(list(QueryComplexity))
            )
            conversation_history.append({
                "role": MessageRole.USER.value,
                "content": user_query
            })
            
            # Add assistant message
            conversation_history.append({
                "role": MessageRole.ASSISTANT.value,
                "content": f"This is a mock response to: {user_query}"
            })
        
        return conversation_history
    
    def _generate_context(self, agent_type: AgentType) -> Dict[str, Any]:
        """
        Generate context for the specified agent type.
        
        Args:
            agent_type: Agent type
            
        Returns:
            Generated context
        """
        # Generate context based on agent type
        if agent_type == AgentType.DOCUMENTATION:
            return {
                "aircraft_type": random.choice(["Boeing 737", "Airbus A320", "Boeing 777", "Airbus A350"]),
                "document_types": random.sample(["manual", "bulletin", "directive", "specification"], k=random.randint(1, 3)),
                "user_preferences": {
                    "detail_level": random.choice(["basic", "detailed", "comprehensive"]),
                    "include_diagrams": random.choice([True, False]),
                    "include_references": random.choice([True, False])
                }
            }
        elif agent_type == AgentType.TROUBLESHOOTING:
            return {
                "aircraft_type": random.choice(["Boeing 737", "Airbus A320", "Boeing 777", "Airbus A350"]),
                "system": random.choice(["hydraulic", "electrical", "avionics", "engines", "fuel", "landing gear"]),
                "maintenance_history": [
                    {
                        "date": "2023-01-15",
                        "description": "Routine maintenance check"
                    },
                    {
                        "date": "2023-03-22",
                        "description": "Component replacement"
                    }
                ],
                "environment": {
                    "location": random.choice(["hangar", "ramp", "in flight"]),
                    "weather": random.choice(["normal", "extreme heat", "extreme cold", "high humidity"])
                }
            }
        elif agent_type == AgentType.MAINTENANCE:
            return {
                "aircraft_type": random.choice(["Boeing 737", "Airbus A320", "Boeing 777", "Airbus A350"]),
                "aircraft_model": random.choice(["737-800", "A320neo", "777-300ER", "A350-900"]),
                "system": random.choice(["hydraulic", "electrical", "avionics", "engines", "fuel", "landing gear"]),
                "maintenance_type": random.choice(["routine", "scheduled", "unscheduled", "major overhaul"]),
                "available_resources": {
                    "personnel": random.randint(1, 5),
                    "time_available": f"{random.randint(1, 24)} hours",
                    "special_equipment": random.choice([True, False])
                },
                "regulatory_requirements": random.choice(["FAA", "EASA", "CASA", "Transport Canada"])
            }
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")
    
    def _get_expected_response_patterns(
        self, agent_type: AgentType, complexity: QueryComplexity
    ) -> List[str]:
        """
        Get expected response patterns for the specified agent type and complexity.
        
        Args:
            agent_type: Agent type
            complexity: Query complexity
            
        Returns:
            List of expected response patterns
        """
        return self.EXPECTED_RESPONSE_PATTERNS[agent_type][complexity]


# Example usage
if __name__ == "__main__":
    # Create generator
    generator = AgentTestCaseGenerator(seed=42)
    
    # Generate test case for documentation agent
    test_case = generator.generate_test_case(
        agent_type=AgentType.DOCUMENTATION,
        complexity=QueryComplexity.MODERATE,
        include_conversation_history=True,
        include_context=True
    )
    
    # Print test case
    import json
    print(json.dumps(test_case, indent=2))
    
    # Generate multiple test cases
    test_cases = generator.generate_test_cases(
        count=5,
        agent_types=[AgentType.DOCUMENTATION, AgentType.TROUBLESHOOTING],
        complexities=[QueryComplexity.SIMPLE, QueryComplexity.MODERATE]
    )
    
    # Print test cases
    print(f"Generated {len(test_cases)} test cases")
