"""
Utilities for simulating user inputs and contexts.

This module provides utilities for simulating different user inputs and contexts
for testing agent components.
"""
import random
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

from app.models.conversation import AgentType, MessageRole, Conversation, Message
from app.models.context import ContextWindow, ContextItem, ContextType, ContextPriority


class InputSimulator:
    """
    Simulator for user inputs and contexts.

    This class provides methods for simulating different user inputs and contexts
    for testing agent components.
    """

    # Sample user queries for different agent types
    SAMPLE_QUERIES = {
        AgentType.DOCUMENTATION: [
            "Where can I find information about the landing gear maintenance?",
            "What are the specifications for the hydraulic system?",
            "Show me the latest service bulletin for the engines.",
            "What's the procedure for checking the fuel system?",
            "Find documentation about the avionics system."
        ],
        AgentType.TROUBLESHOOTING: [
            "The hydraulic pressure is low. What could be causing this?",
            "The navigation system is showing errors. How do I diagnose this?",
            "The APU won't start. What are the possible causes?",
            "There's a strange noise coming from the landing gear. What should I check?",
            "The cabin pressure warning light is on. What's the troubleshooting procedure?"
        ],
        AgentType.MAINTENANCE: [
            "Generate a maintenance procedure for replacing the fuel pump.",
            "Create a checklist for inspecting the landing gear.",
            "What's the procedure for servicing the hydraulic system?",
            "Generate a maintenance plan for the avionics system.",
            "Create a procedure for testing the emergency systems."
        ]
    }

    # Sample aircraft types
    AIRCRAFT_TYPES = [
        "Boeing 737-800",
        "Airbus A320neo",
        "Boeing 777-300ER",
        "Airbus A350-900",
        "Embraer E190",
        "Bombardier CRJ-900",
        "ATR 72-600"
    ]

    # Sample aircraft systems
    AIRCRAFT_SYSTEMS = [
        "Hydraulic",
        "Electrical",
        "Avionics",
        "Fuel",
        "Landing Gear",
        "Environmental Control",
        "Flight Controls",
        "Engines",
        "APU",
        "Pneumatic"
    ]

    # Sample maintenance types
    MAINTENANCE_TYPES = [
        "Inspection",
        "Replacement",
        "Overhaul",
        "Testing",
        "Servicing",
        "Troubleshooting",
        "Modification",
        "Repair"
    ]

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the input simulator.

        Args:
            seed: Optional random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)

    def generate_random_query(self, agent_type: AgentType) -> str:
        """
        Generate a random query for the specified agent type.

        Args:
            agent_type: Agent type

        Returns:
            Random query
        """
        return random.choice(self.SAMPLE_QUERIES[agent_type])

    def generate_conversation(
        self,
        agent_type: AgentType,
        num_turns: int = 3,
        include_system_message: bool = True
    ) -> Conversation:
        """
        Generate a simulated conversation.

        Args:
            agent_type: Agent type
            num_turns: Number of conversation turns
            include_system_message: Whether to include a system message

        Returns:
            Simulated conversation
        """
        # Create conversation
        conversation = Conversation(
            id=random.randint(1, 1000),
            conversation_id=str(uuid.uuid4()),
            user_id=random.randint(1, 100),
            agent_type=agent_type,
            created_at=datetime.now() - timedelta(hours=1),
            updated_at=datetime.now(),
            is_active=True
        )

        # Add messages
        messages = []

        # Add system message if requested
        if include_system_message:
            messages.append(
                Message(
                    id=random.randint(1, 1000),
                    conversation_id=conversation.id,
                    role=MessageRole.SYSTEM,
                    content=f"You are a helpful {agent_type.value} assistant.",
                    created_at=datetime.now() - timedelta(hours=1),
                    token_count=20
                )
            )

        # Add conversation turns
        for i in range(num_turns):
            # Add user message
            user_query = self.generate_random_query(agent_type)
            messages.append(
                Message(
                    id=random.randint(1001, 2000) + i * 2,
                    conversation_id=conversation.id,
                    role=MessageRole.USER,
                    content=user_query,
                    created_at=datetime.now() - timedelta(minutes=30) + timedelta(minutes=i * 10),
                    token_count=len(user_query.split())
                )
            )

            # Add assistant message
            assistant_response = f"This is a simulated response to: {user_query}"
            messages.append(
                Message(
                    id=random.randint(2001, 3000) + i * 2,
                    conversation_id=conversation.id,
                    role=MessageRole.ASSISTANT,
                    content=assistant_response,
                    created_at=datetime.now() - timedelta(minutes=25) + timedelta(minutes=i * 10),
                    token_count=len(assistant_response.split())
                )
            )

        # Set conversation messages
        conversation.messages = messages

        return conversation

    def generate_context_window(
        self, conversation_id: int, num_items: int = 5
    ) -> Tuple[ContextWindow, List[ContextItem]]:
        """
        Generate a simulated context window with items.

        Args:
            conversation_id: Conversation ID
            num_items: Number of context items

        Returns:
            Tuple of (context window, context items)
        """
        # Create context window
        window = ContextWindow(
            id=random.randint(1, 1000),
            conversation_id=conversation_id,
            created_at=datetime.now() - timedelta(hours=1),
            updated_at=datetime.now(),
            is_active=True,
            max_tokens=4000,
            current_tokens=0
        )

        # Create context items
        items = []
        for i in range(num_items):
            # Determine item type
            item_type = random.choice(list(ContextType))

            # Create content based on type
            if item_type == ContextType.USER_PREFERENCE:
                content = {
                    "preference_type": random.choice(["detail_level", "format", "focus"]),
                    "value": random.choice(["high", "medium", "low", "technical", "simple"])
                }
            elif item_type == ContextType.AIRCRAFT_INFO:
                content = {
                    "aircraft_type": random.choice(self.AIRCRAFT_TYPES),
                    "system": random.choice(self.AIRCRAFT_SYSTEMS)
                }
            elif item_type == ContextType.MAINTENANCE_INFO:
                content = {
                    "maintenance_type": random.choice(self.MAINTENANCE_TYPES),
                    "component": random.choice(["pump", "valve", "sensor", "actuator", "controller"])
                }
            else:
                content = {
                    "key": f"value_{i}",
                    "description": f"Sample content for item {i}"
                }

            # Create item
            item = ContextItem(
                id=random.randint(1001, 2000) + i,
                window_id=window.id,
                type=item_type,
                priority=random.choice(list(ContextPriority)),
                content=content,
                token_count=random.randint(10, 100),
                created_at=datetime.now() - timedelta(minutes=30) + timedelta(minutes=i * 5),
                is_included=True,
                relevance_score=random.uniform(0.5, 1.0)
            )

            items.append(item)

            # Update window token count
            window.current_tokens += item.token_count

        return window, items

    def generate_agent_context(self, agent_type: AgentType) -> Dict[str, Any]:
        """
        Generate context for the specified agent type.

        Args:
            agent_type: Agent type

        Returns:
            Generated context
        """
        # Base context for all agent types
        context = {
            "user_id": random.randint(1, 100),
            "timestamp": datetime.now().isoformat(),
            "session_id": str(uuid.uuid4())
        }

        # Add agent-specific context
        if agent_type == AgentType.DOCUMENTATION:
            context.update({
                "aircraft_type": random.choice(self.AIRCRAFT_TYPES),
                "document_types": random.sample(["manual", "bulletin", "directive", "specification"], k=random.randint(1, 3)),
                "user_preferences": {
                    "detail_level": random.choice(["basic", "detailed", "comprehensive"]),
                    "include_diagrams": random.choice([True, False]),
                    "include_references": random.choice([True, False])
                }
            })
        elif agent_type == AgentType.TROUBLESHOOTING:
            context.update({
                "aircraft_type": random.choice(self.AIRCRAFT_TYPES),
                "system": random.choice(self.AIRCRAFT_SYSTEMS),
                "symptoms": random.sample([
                    "warning light", "unusual noise", "vibration", "leak", "no power",
                    "intermittent failure", "error message", "reduced performance"
                ], k=random.randint(1, 3)),
                "maintenance_history": [
                    {
                        "date": (datetime.now() - timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d"),
                        "description": f"Maintenance on {random.choice(self.AIRCRAFT_SYSTEMS)} system"
                    }
                    for _ in range(random.randint(1, 3))
                ]
            })
        elif agent_type == AgentType.MAINTENANCE:
            context.update({
                "aircraft_type": random.choice(self.AIRCRAFT_TYPES),
                "system": random.choice(self.AIRCRAFT_SYSTEMS),
                "maintenance_type": random.choice(self.MAINTENANCE_TYPES),
                "available_resources": {
                    "personnel": random.randint(1, 5),
                    "time_available": f"{random.randint(1, 24)} hours",
                    "special_equipment": random.choice([True, False])
                },
                "regulatory_requirements": random.choice(["FAA", "EASA", "CASA", "Transport Canada"])
            })

        return context

    def generate_conversation_history(
        self, agent_type: AgentType, num_turns: int = 3
    ) -> List[Dict[str, str]]:
        """
        Generate conversation history for LLM context.

        Args:
            agent_type: Agent type
            num_turns: Number of conversation turns

        Returns:
            List of conversation messages
        """
        # Create conversation history
        history = []

        # Add system message
        history.append({
            "role": "system",
            "content": f"You are a helpful {agent_type.value} assistant."
        })

        # Add conversation turns
        for _ in range(num_turns):
            # Add user message
            user_query = self.generate_random_query(agent_type)
            history.append({
                "role": "user",
                "content": user_query
            })

            # Add assistant message
            history.append({
                "role": "assistant",
                "content": f"This is a simulated response to: {user_query}"
            })

        return history


    def generate_documentation_content(self, aircraft_type: str, system: str) -> str:
        """
        Generate documentation content for the specified aircraft type and system.

        Args:
            aircraft_type: Aircraft type
            system: Aircraft system

        Returns:
            Generated documentation content
        """
        # Generate random documentation content
        paragraphs = []

        # Introduction
        paragraphs.append(f"This document provides information about the {system} system for the {aircraft_type} aircraft. "
                         f"It includes specifications, maintenance procedures, and troubleshooting guidelines.")

        # Specifications
        paragraphs.append(f"## Specifications\n\n"
                         f"The {system} system on the {aircraft_type} consists of the following components:\n"
                         f"- Primary {system.lower()} control unit\n"
                         f"- Secondary {system.lower()} control unit\n"
                         f"- {system} sensors (quantity: {random.randint(2, 8)})\n"
                         f"- {system} actuators (quantity: {random.randint(1, 6)})\n"
                         f"- {system} monitoring system")

        # Maintenance procedures
        paragraphs.append(f"## Maintenance Procedures\n\n"
                         f"Regular maintenance of the {system} system includes:\n"
                         f"1. Inspection every {random.randint(100, 1000)} flight hours\n"
                         f"2. Functional testing every {random.randint(500, 2000)} flight hours\n"
                         f"3. Component replacement according to the maintenance schedule\n"
                         f"4. Software updates as specified in service bulletins")

        # Troubleshooting
        paragraphs.append(f"## Troubleshooting\n\n"
                         f"Common issues with the {system} system include:\n"
                         f"- Sensor failures\n"
                         f"- Control unit errors\n"
                         f"- Actuator malfunctions\n"
                         f"- Wiring problems\n\n"
                         f"Refer to the troubleshooting guide for detailed procedures.")

        # References
        paragraphs.append(f"## References\n\n"
                         f"- {aircraft_type} Maintenance Manual, Chapter {random.randint(20, 80)}\n"
                         f"- {system} Component Maintenance Manual\n"
                         f"- Service Bulletin SB-{aircraft_type.replace(' ', '-')}-{random.randint(100, 999)}")

        return "\n\n".join(paragraphs)

    def generate_troubleshooting_description(self, aircraft_type: str, system: str, symptom: str) -> str:
        """
        Generate troubleshooting description for the specified aircraft type, system, and symptom.

        Args:
            aircraft_type: Aircraft type
            system: Aircraft system
            symptom: Symptom

        Returns:
            Generated troubleshooting description
        """
        return (f"This troubleshooting guide addresses {symptom} issues in the {system} system "
                f"of the {aircraft_type} aircraft. The {symptom} may indicate various underlying "
                f"problems that require systematic diagnosis and resolution.")

    def generate_troubleshooting_steps(self, aircraft_type: str, system: str, symptom: str) -> List[str]:
        """
        Generate troubleshooting steps for the specified aircraft type, system, and symptom.

        Args:
            aircraft_type: Aircraft type
            system: Aircraft system
            symptom: Symptom

        Returns:
            List of troubleshooting steps
        """
        steps = [
            f"1. Initial Assessment: Verify the {symptom} and collect all relevant information.",
            f"2. Visual Inspection: Check the {system} system components for visible damage or irregularities.",
            f"3. System Test: Perform a functional test of the {system} system using the maintenance computer.",
            f"4. Component Check: Test individual components of the {system} system.",
            f"5. Wiring Inspection: Check wiring and connections related to the {system} system.",
            f"6. Replace/Repair: Replace or repair faulty components as identified.",
            f"7. Verification: Perform a final test to ensure the {symptom} has been resolved."
        ]

        return steps

    def generate_maintenance_description(self, aircraft_type: str, system: str, maintenance_type: str) -> str:
        """
        Generate maintenance description for the specified aircraft type, system, and maintenance type.

        Args:
            aircraft_type: Aircraft type
            system: Aircraft system
            maintenance_type: Maintenance type

        Returns:
            Generated maintenance description
        """
        return (f"This {maintenance_type.lower()} procedure applies to the {system} system "
                f"of the {aircraft_type} aircraft. It provides step-by-step instructions "
                f"for performing {maintenance_type.lower()} tasks safely and effectively.")

    def generate_maintenance_tools(self, aircraft_type: str, system: str, maintenance_type: str) -> List[str]:
        """
        Generate maintenance tools for the specified aircraft type, system, and maintenance type.

        Args:
            aircraft_type: Aircraft type
            system: Aircraft system
            maintenance_type: Maintenance type

        Returns:
            List of maintenance tools
        """
        common_tools = [
            "Standard toolkit",
            "Torque wrench",
            "Multimeter",
            "Pressure gauge",
            "Inspection mirror",
            "Flashlight",
            "Safety equipment"
        ]

        specific_tools = [
            f"{system} test equipment",
            f"{maintenance_type} special tool kit",
            f"{aircraft_type} maintenance computer",
            f"{system} calibration device"
        ]

        # Select a random subset of tools
        tools = common_tools + random.sample(specific_tools, k=random.randint(1, len(specific_tools)))

        return tools

    def generate_maintenance_safety(self, aircraft_type: str, system: str, maintenance_type: str) -> List[str]:
        """
        Generate maintenance safety precautions for the specified aircraft type, system, and maintenance type.

        Args:
            aircraft_type: Aircraft type
            system: Aircraft system
            maintenance_type: Maintenance type

        Returns:
            List of safety precautions
        """
        safety_precautions = [
            "Ensure aircraft is properly grounded",
            "Disconnect electrical power before starting work",
            "Use appropriate personal protective equipment",
            "Follow all safety procedures in the maintenance manual",
            f"Be aware of specific {system} system hazards",
            "Secure all tools and equipment",
            "Verify work area is clear before system testing"
        ]

        return safety_precautions

    def generate_maintenance_steps(self, aircraft_type: str, system: str, maintenance_type: str) -> List[str]:
        """
        Generate maintenance steps for the specified aircraft type, system, and maintenance type.

        Args:
            aircraft_type: Aircraft type
            system: Aircraft system
            maintenance_type: Maintenance type

        Returns:
            List of maintenance steps
        """
        steps = [
            f"1. Preparation: Gather all necessary tools and equipment for {system} system {maintenance_type.lower()}.",
            f"2. Access: Gain access to the {system} system components according to the maintenance manual.",
            f"3. Inspection: Perform a visual inspection of the {system} system components.",
            f"4. {maintenance_type}: Perform the {maintenance_type.lower()} procedure as specified.",
            f"5. Testing: Test the {system} system functionality after {maintenance_type.lower()}.",
            f"6. Documentation: Complete all required maintenance records.",
            f"7. Return to Service: Prepare the aircraft for return to service."
        ]

        return steps

    def generate_documentation_conversation(self) -> List[Dict[str, str]]:
        """
        Generate a documentation conversation.

        Returns:
            List of conversation messages
        """
        aircraft_type = random.choice(self.AIRCRAFT_TYPES)
        system = random.choice(self.AIRCRAFT_SYSTEMS)

        conversation = [
            {
                "role": "user",
                "content": f"Where can I find information about the {system} system on the {aircraft_type}?"
            },
            {
                "role": "assistant",
                "content": f"You can find information about the {system} system in Chapter {random.randint(20, 80)} of the {aircraft_type} Maintenance Manual. Would you like me to provide a summary of the key information?"
            },
            {
                "role": "user",
                "content": "Yes, please provide a summary."
            },
            {
                "role": "assistant",
                "content": self.generate_documentation_content(aircraft_type, system)
            }
        ]

        return conversation

    def generate_troubleshooting_conversation(self) -> List[Dict[str, str]]:
        """
        Generate a troubleshooting conversation.

        Returns:
            List of conversation messages
        """
        aircraft_type = random.choice(self.AIRCRAFT_TYPES)
        system = random.choice(self.AIRCRAFT_SYSTEMS)
        symptom = random.choice([
            "warning light", "unusual noise", "vibration", "leak",
            "no power", "intermittent failure", "error message"
        ])

        conversation = [
            {
                "role": "user",
                "content": f"I'm seeing a {symptom} in the {system} system on our {aircraft_type}. How should I troubleshoot this?"
            },
            {
                "role": "assistant",
                "content": f"I'll help you troubleshoot the {symptom} in the {system} system. Let me provide a systematic approach to diagnose and resolve this issue."
            },
            {
                "role": "user",
                "content": "Great, what steps should I follow?"
            },
            {
                "role": "assistant",
                "content": self.generate_troubleshooting_description(aircraft_type, system, symptom) + "\n\n" + "\n".join(self.generate_troubleshooting_steps(aircraft_type, system, symptom))
            }
        ]

        return conversation

    def generate_maintenance_conversation(self) -> List[Dict[str, str]]:
        """
        Generate a maintenance conversation.

        Returns:
            List of conversation messages
        """
        aircraft_type = random.choice(self.AIRCRAFT_TYPES)
        system = random.choice(self.AIRCRAFT_SYSTEMS)
        maintenance_type = random.choice(self.MAINTENANCE_TYPES)

        conversation = [
            {
                "role": "user",
                "content": f"I need to perform {maintenance_type} on the {system} system of our {aircraft_type}. Can you provide the procedure?"
            },
            {
                "role": "assistant",
                "content": f"I'll help you with the {maintenance_type} procedure for the {system} system on the {aircraft_type}. Let me provide the necessary information."
            },
            {
                "role": "user",
                "content": "What tools will I need and what are the safety precautions?"
            },
            {
                "role": "assistant",
                "content": (f"# {maintenance_type} Procedure for {system} System on {aircraft_type}\n\n"
                           f"{self.generate_maintenance_description(aircraft_type, system, maintenance_type)}\n\n"
                           f"## Required Tools\n" + "\n".join([f"- {tool}" for tool in self.generate_maintenance_tools(aircraft_type, system, maintenance_type)]) + "\n\n"
                           f"## Safety Precautions\n" + "\n".join([f"- {precaution}" for precaution in self.generate_maintenance_safety(aircraft_type, system, maintenance_type)]) + "\n\n"
                           f"## Procedure Steps\n" + "\n".join(self.generate_maintenance_steps(aircraft_type, system, maintenance_type)))
            }
        ]

        return conversation


# Example usage
if __name__ == "__main__":
    # Create simulator
    simulator = InputSimulator(seed=42)

    # Generate random query
    query = simulator.generate_random_query(AgentType.DOCUMENTATION)
    print(f"Random query: {query}")

    # Generate conversation
    conversation = simulator.generate_conversation(AgentType.TROUBLESHOOTING, num_turns=2)
    print(f"Conversation: {conversation.conversation_id}")
    print(f"Number of messages: {len(conversation.messages)}")

    # Generate context window
    window, items = simulator.generate_context_window(conversation_id=conversation.id, num_items=3)
    print(f"Context window: {window.id}")
    print(f"Number of items: {len(items)}")

    # Generate agent context
    context = simulator.generate_agent_context(AgentType.MAINTENANCE)
    print(f"Agent context: {context}")

    # Generate conversation history
    history = simulator.generate_conversation_history(AgentType.DOCUMENTATION, num_turns=2)
    print(f"Conversation history: {len(history)} messages")
