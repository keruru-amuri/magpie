"""
Synthetic test data generator for the MAGPIE platform.

This module provides utilities for generating synthetic test data.
"""
import os
import json
import random
import logging
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path

from tests.framework.ci_cd.data_management import (
    DataManager, DataSet, DataItem, DataCategory, DataFormat
)
from tests.framework.utilities.input_simulator import InputSimulator

# Configure logging
logger = logging.getLogger(__name__)


class DataGenerator:
    """
    Generator for synthetic test data.
    """
    
    def __init__(
        self,
        data_manager: Optional[DataManager] = None,
        input_simulator: Optional[InputSimulator] = None,
        output_dir: Optional[Union[str, Path]] = None,
        seed: Optional[int] = None
    ):
        """
        Initialize data generator.
        
        Args:
            data_manager: Optional data manager
            input_simulator: Optional input simulator
            output_dir: Optional output directory
            seed: Optional random seed
        """
        self.data_manager = data_manager or DataManager()
        self.input_simulator = input_simulator or InputSimulator(seed=seed)
        self.output_dir = output_dir or Path("generated_data")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        if seed is not None:
            random.seed(seed)
    
    def generate_documentation_data(
        self,
        count: int = 10,
        set_name: str = "Documentation Data",
        tags: Optional[List[str]] = None
    ) -> DataSet:
        """
        Generate documentation data.
        
        Args:
            count: Number of items to generate
            set_name: Data set name
            tags: Optional tags
            
        Returns:
            Data set
        """
        # Create data set
        data_set = self.data_manager.create_set(
            name=set_name,
            description=f"Generated documentation data ({count} items)",
            tags=tags or ["documentation", "generated"]
        )
        
        # Generate items
        for i in range(count):
            # Generate content
            aircraft_type = random.choice(self.input_simulator.AIRCRAFT_TYPES)
            system = random.choice(self.input_simulator.AIRCRAFT_SYSTEMS)
            
            content = {
                "title": f"{aircraft_type} {system} Documentation",
                "document_id": f"DOC-{random.randint(1000, 9999)}",
                "revision": f"Rev {random.choice(['A', 'B', 'C', 'D', 'E'])}",
                "date": (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
                "content": self.input_simulator.generate_documentation_content(aircraft_type, system)
            }
            
            # Save to file
            file_path = Path(self.output_dir) / f"doc_{i}.json"
            
            with open(file_path, "w") as f:
                json.dump(content, f, indent=2)
            
            # Add to data set
            self.data_manager.add_item(
                set_id=data_set.id,
                name=content["title"],
                category=DataCategory.DOCUMENTATION,
                format=DataFormat.JSON,
                source_path=str(file_path),
                metadata={
                    "aircraft_type": aircraft_type,
                    "system": system,
                    "document_id": content["document_id"],
                    "revision": content["revision"],
                    "date": content["date"]
                },
                tags=[aircraft_type.lower(), system.lower(), "documentation"]
            )
        
        return data_set
    
    def generate_troubleshooting_data(
        self,
        count: int = 10,
        set_name: str = "Troubleshooting Data",
        tags: Optional[List[str]] = None
    ) -> DataSet:
        """
        Generate troubleshooting data.
        
        Args:
            count: Number of items to generate
            set_name: Data set name
            tags: Optional tags
            
        Returns:
            Data set
        """
        # Create data set
        data_set = self.data_manager.create_set(
            name=set_name,
            description=f"Generated troubleshooting data ({count} items)",
            tags=tags or ["troubleshooting", "generated"]
        )
        
        # Generate items
        for i in range(count):
            # Generate content
            aircraft_type = random.choice(self.input_simulator.AIRCRAFT_TYPES)
            system = random.choice(self.input_simulator.AIRCRAFT_SYSTEMS)
            symptom = random.choice([
                "warning light", "unusual noise", "vibration", "leak",
                "no power", "intermittent failure", "error message"
            ])
            
            content = {
                "title": f"{aircraft_type} {system} Troubleshooting - {symptom}",
                "case_id": f"CASE-{random.randint(1000, 9999)}",
                "date": (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
                "aircraft_type": aircraft_type,
                "system": system,
                "symptom": symptom,
                "description": self.input_simulator.generate_troubleshooting_description(aircraft_type, system, symptom),
                "steps": self.input_simulator.generate_troubleshooting_steps(aircraft_type, system, symptom)
            }
            
            # Save to file
            file_path = Path(self.output_dir) / f"troubleshooting_{i}.json"
            
            with open(file_path, "w") as f:
                json.dump(content, f, indent=2)
            
            # Add to data set
            self.data_manager.add_item(
                set_id=data_set.id,
                name=content["title"],
                category=DataCategory.TROUBLESHOOTING,
                format=DataFormat.JSON,
                source_path=str(file_path),
                metadata={
                    "aircraft_type": aircraft_type,
                    "system": system,
                    "symptom": symptom,
                    "case_id": content["case_id"],
                    "date": content["date"]
                },
                tags=[aircraft_type.lower(), system.lower(), symptom.lower(), "troubleshooting"]
            )
        
        return data_set
    
    def generate_maintenance_data(
        self,
        count: int = 10,
        set_name: str = "Maintenance Data",
        tags: Optional[List[str]] = None
    ) -> DataSet:
        """
        Generate maintenance data.
        
        Args:
            count: Number of items to generate
            set_name: Data set name
            tags: Optional tags
            
        Returns:
            Data set
        """
        # Create data set
        data_set = self.data_manager.create_set(
            name=set_name,
            description=f"Generated maintenance data ({count} items)",
            tags=tags or ["maintenance", "generated"]
        )
        
        # Generate items
        for i in range(count):
            # Generate content
            aircraft_type = random.choice(self.input_simulator.AIRCRAFT_TYPES)
            system = random.choice(self.input_simulator.AIRCRAFT_SYSTEMS)
            maintenance_type = random.choice(self.input_simulator.MAINTENANCE_TYPES)
            
            content = {
                "title": f"{aircraft_type} {system} {maintenance_type}",
                "procedure_id": f"PROC-{random.randint(1000, 9999)}",
                "revision": f"Rev {random.choice(['A', 'B', 'C', 'D', 'E'])}",
                "date": (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
                "aircraft_type": aircraft_type,
                "system": system,
                "maintenance_type": maintenance_type,
                "description": self.input_simulator.generate_maintenance_description(aircraft_type, system, maintenance_type),
                "tools": self.input_simulator.generate_maintenance_tools(aircraft_type, system, maintenance_type),
                "safety": self.input_simulator.generate_maintenance_safety(aircraft_type, system, maintenance_type),
                "steps": self.input_simulator.generate_maintenance_steps(aircraft_type, system, maintenance_type)
            }
            
            # Save to file
            file_path = Path(self.output_dir) / f"maintenance_{i}.json"
            
            with open(file_path, "w") as f:
                json.dump(content, f, indent=2)
            
            # Add to data set
            self.data_manager.add_item(
                set_id=data_set.id,
                name=content["title"],
                category=DataCategory.MAINTENANCE,
                format=DataFormat.JSON,
                source_path=str(file_path),
                metadata={
                    "aircraft_type": aircraft_type,
                    "system": system,
                    "maintenance_type": maintenance_type,
                    "procedure_id": content["procedure_id"],
                    "revision": content["revision"],
                    "date": content["date"]
                },
                tags=[aircraft_type.lower(), system.lower(), maintenance_type.lower(), "maintenance"]
            )
        
        return data_set
    
    def generate_conversation_data(
        self,
        count: int = 10,
        set_name: str = "Conversation Data",
        tags: Optional[List[str]] = None
    ) -> DataSet:
        """
        Generate conversation data.
        
        Args:
            count: Number of items to generate
            set_name: Data set name
            tags: Optional tags
            
        Returns:
            Data set
        """
        # Create data set
        data_set = self.data_manager.create_set(
            name=set_name,
            description=f"Generated conversation data ({count} items)",
            tags=tags or ["conversation", "generated"]
        )
        
        # Generate items
        for i in range(count):
            # Generate content
            conversation_type = random.choice(["documentation", "troubleshooting", "maintenance"])
            
            if conversation_type == "documentation":
                conversation = self.input_simulator.generate_documentation_conversation()
            elif conversation_type == "troubleshooting":
                conversation = self.input_simulator.generate_troubleshooting_conversation()
            else:
                conversation = self.input_simulator.generate_maintenance_conversation()
            
            content = {
                "conversation_id": f"CONV-{random.randint(1000, 9999)}",
                "date": (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
                "type": conversation_type,
                "messages": conversation
            }
            
            # Save to file
            file_path = Path(self.output_dir) / f"conversation_{i}.json"
            
            with open(file_path, "w") as f:
                json.dump(content, f, indent=2)
            
            # Add to data set
            self.data_manager.add_item(
                set_id=data_set.id,
                name=f"Conversation {content['conversation_id']}",
                category=DataCategory.CONVERSATION,
                format=DataFormat.JSON,
                source_path=str(file_path),
                metadata={
                    "conversation_id": content["conversation_id"],
                    "type": conversation_type,
                    "date": content["date"],
                    "message_count": len(conversation)
                },
                tags=[conversation_type, "conversation"]
            )
        
        return data_set
    
    def generate_reference_data(
        self,
        set_name: str = "Reference Data",
        tags: Optional[List[str]] = None
    ) -> DataSet:
        """
        Generate reference data.
        
        Args:
            set_name: Data set name
            tags: Optional tags
            
        Returns:
            Data set
        """
        # Create data set
        data_set = self.data_manager.create_set(
            name=set_name,
            description="Generated reference data",
            tags=tags or ["reference", "generated"]
        )
        
        # Generate aircraft reference data
        aircraft_data = {}
        
        for aircraft_type in self.input_simulator.AIRCRAFT_TYPES:
            aircraft_data[aircraft_type] = {
                "manufacturer": random.choice(["Boeing", "Airbus", "Embraer", "Bombardier", "Cessna"]),
                "model": f"{aircraft_type}-{random.randint(100, 999)}",
                "systems": {},
                "specifications": {
                    "length": f"{random.randint(20, 80)} m",
                    "wingspan": f"{random.randint(20, 80)} m",
                    "height": f"{random.randint(5, 20)} m",
                    "max_takeoff_weight": f"{random.randint(10000, 500000)} kg",
                    "max_range": f"{random.randint(1000, 15000)} km",
                    "max_speed": f"{random.randint(700, 1000)} km/h",
                    "max_altitude": f"{random.randint(30000, 45000)} ft"
                }
            }
            
            for system in self.input_simulator.AIRCRAFT_SYSTEMS:
                aircraft_data[aircraft_type]["systems"][system] = {
                    "components": [f"Component {i+1}" for i in range(random.randint(3, 10))],
                    "maintenance_interval": f"{random.randint(100, 5000)} hours",
                    "inspection_interval": f"{random.randint(10, 500)} hours"
                }
        
        # Save to file
        aircraft_file_path = Path(self.output_dir) / "aircraft_reference.json"
        
        with open(aircraft_file_path, "w") as f:
            json.dump(aircraft_data, f, indent=2)
        
        # Add to data set
        self.data_manager.add_item(
            set_id=data_set.id,
            name="Aircraft Reference Data",
            category=DataCategory.REFERENCE,
            format=DataFormat.JSON,
            source_path=str(aircraft_file_path),
            metadata={
                "aircraft_count": len(self.input_simulator.AIRCRAFT_TYPES),
                "system_count": len(self.input_simulator.AIRCRAFT_SYSTEMS)
            },
            tags=["aircraft", "reference"]
        )
        
        # Generate maintenance reference data
        maintenance_data = {}
        
        for maintenance_type in self.input_simulator.MAINTENANCE_TYPES:
            maintenance_data[maintenance_type] = {
                "description": f"Standard {maintenance_type} procedure",
                "required_certifications": [f"Certification {i+1}" for i in range(random.randint(1, 3))],
                "typical_duration": f"{random.randint(1, 48)} hours",
                "common_tools": [f"Tool {i+1}" for i in range(random.randint(3, 10))],
                "safety_equipment": [f"Safety Equipment {i+1}" for i in range(random.randint(2, 5))]
            }
        
        # Save to file
        maintenance_file_path = Path(self.output_dir) / "maintenance_reference.json"
        
        with open(maintenance_file_path, "w") as f:
            json.dump(maintenance_data, f, indent=2)
        
        # Add to data set
        self.data_manager.add_item(
            set_id=data_set.id,
            name="Maintenance Reference Data",
            category=DataCategory.REFERENCE,
            format=DataFormat.JSON,
            source_path=str(maintenance_file_path),
            metadata={
                "maintenance_type_count": len(self.input_simulator.MAINTENANCE_TYPES)
            },
            tags=["maintenance", "reference"]
        )
        
        return data_set
    
    def generate_mock_data(
        self,
        set_name: str = "Mock Data",
        tags: Optional[List[str]] = None
    ) -> DataSet:
        """
        Generate mock data for testing.
        
        Args:
            set_name: Data set name
            tags: Optional tags
            
        Returns:
            Data set
        """
        # Create data set
        data_set = self.data_manager.create_set(
            name=set_name,
            description="Generated mock data for testing",
            tags=tags or ["mock", "testing", "generated"]
        )
        
        # Generate mock API responses
        api_responses = {
            "documentation": {
                "search": {
                    "query": "Boeing 737 maintenance manual",
                    "results": [
                        {
                            "id": "DOC-1001",
                            "title": "Boeing 737 Maintenance Manual",
                            "revision": "Rev C",
                            "date": "2023-01-15",
                            "excerpt": "This manual provides maintenance procedures for the Boeing 737 aircraft."
                        },
                        {
                            "id": "DOC-1002",
                            "title": "Boeing 737 Component Maintenance Manual",
                            "revision": "Rev B",
                            "date": "2023-02-20",
                            "excerpt": "This manual provides maintenance procedures for Boeing 737 components."
                        }
                    ]
                },
                "get": {
                    "id": "DOC-1001",
                    "title": "Boeing 737 Maintenance Manual",
                    "revision": "Rev C",
                    "date": "2023-01-15",
                    "content": "This is a mock content for the Boeing 737 Maintenance Manual."
                }
            },
            "troubleshooting": {
                "search": {
                    "query": "Boeing 737 engine vibration",
                    "results": [
                        {
                            "id": "CASE-2001",
                            "title": "Engine Vibration Troubleshooting",
                            "aircraft_type": "Boeing 737",
                            "system": "Engine",
                            "date": "2023-03-10"
                        },
                        {
                            "id": "CASE-2002",
                            "title": "High Engine Vibration During Cruise",
                            "aircraft_type": "Boeing 737",
                            "system": "Engine",
                            "date": "2023-04-05"
                        }
                    ]
                },
                "get": {
                    "id": "CASE-2001",
                    "title": "Engine Vibration Troubleshooting",
                    "aircraft_type": "Boeing 737",
                    "system": "Engine",
                    "date": "2023-03-10",
                    "description": "This is a mock troubleshooting procedure for Boeing 737 engine vibration.",
                    "steps": [
                        "Step 1: Check engine mounts",
                        "Step 2: Inspect fan blades",
                        "Step 3: Check balance"
                    ]
                }
            },
            "maintenance": {
                "search": {
                    "query": "Boeing 737 tire replacement",
                    "results": [
                        {
                            "id": "PROC-3001",
                            "title": "Main Landing Gear Tire Replacement",
                            "aircraft_type": "Boeing 737",
                            "system": "Landing Gear",
                            "date": "2023-05-12"
                        },
                        {
                            "id": "PROC-3002",
                            "title": "Nose Landing Gear Tire Replacement",
                            "aircraft_type": "Boeing 737",
                            "system": "Landing Gear",
                            "date": "2023-05-15"
                        }
                    ]
                },
                "get": {
                    "id": "PROC-3001",
                    "title": "Main Landing Gear Tire Replacement",
                    "aircraft_type": "Boeing 737",
                    "system": "Landing Gear",
                    "date": "2023-05-12",
                    "description": "This is a mock procedure for Boeing 737 main landing gear tire replacement.",
                    "tools": ["Jack", "Torque wrench", "Tire pressure gauge"],
                    "steps": [
                        "Step 1: Jack aircraft",
                        "Step 2: Remove wheel assembly",
                        "Step 3: Replace tire",
                        "Step 4: Reinstall wheel assembly",
                        "Step 5: Lower aircraft"
                    ]
                }
            }
        }
        
        # Save to file
        api_file_path = Path(self.output_dir) / "mock_api_responses.json"
        
        with open(api_file_path, "w") as f:
            json.dump(api_responses, f, indent=2)
        
        # Add to data set
        self.data_manager.add_item(
            set_id=data_set.id,
            name="Mock API Responses",
            category=DataCategory.MOCK,
            format=DataFormat.JSON,
            source_path=str(api_file_path),
            metadata={
                "api_count": len(api_responses)
            },
            tags=["api", "mock", "testing"]
        )
        
        # Generate mock user data
        user_data = {
            "users": [
                {
                    "id": "user1",
                    "name": "John Smith",
                    "role": "Maintenance Technician",
                    "certifications": ["A&P License", "Boeing 737 Type Rating"]
                },
                {
                    "id": "user2",
                    "name": "Jane Doe",
                    "role": "Maintenance Engineer",
                    "certifications": ["A&P License", "Airbus A320 Type Rating", "Boeing 737 Type Rating"]
                }
            ],
            "conversations": [
                {
                    "id": "conv1",
                    "user_id": "user1",
                    "date": "2023-06-01",
                    "messages": [
                        {"role": "user", "content": "How do I replace the main landing gear tire on a Boeing 737?"},
                        {"role": "assistant", "content": "Here's the procedure for replacing the main landing gear tire on a Boeing 737..."}
                    ]
                },
                {
                    "id": "conv2",
                    "user_id": "user2",
                    "date": "2023-06-02",
                    "messages": [
                        {"role": "user", "content": "What's the troubleshooting procedure for engine vibration on a Boeing 737?"},
                        {"role": "assistant", "content": "Here's the troubleshooting procedure for engine vibration on a Boeing 737..."}
                    ]
                }
            ]
        }
        
        # Save to file
        user_file_path = Path(self.output_dir) / "mock_user_data.json"
        
        with open(user_file_path, "w") as f:
            json.dump(user_data, f, indent=2)
        
        # Add to data set
        self.data_manager.add_item(
            set_id=data_set.id,
            name="Mock User Data",
            category=DataCategory.MOCK,
            format=DataFormat.JSON,
            source_path=str(user_file_path),
            metadata={
                "user_count": len(user_data["users"]),
                "conversation_count": len(user_data["conversations"])
            },
            tags=["user", "mock", "testing"]
        )
        
        return data_set
    
    def generate_all_data(
        self,
        documentation_count: int = 10,
        troubleshooting_count: int = 10,
        maintenance_count: int = 10,
        conversation_count: int = 10,
        set_name: str = "All Test Data",
        tags: Optional[List[str]] = None
    ) -> DataSet:
        """
        Generate all types of test data.
        
        Args:
            documentation_count: Number of documentation items
            troubleshooting_count: Number of troubleshooting items
            maintenance_count: Number of maintenance items
            conversation_count: Number of conversation items
            set_name: Data set name
            tags: Optional tags
            
        Returns:
            Data set
        """
        # Create data set
        data_set = self.data_manager.create_set(
            name=set_name,
            description="Generated test data of all types",
            tags=tags or ["all", "generated", "test"]
        )
        
        # Generate documentation data
        documentation_set = self.generate_documentation_data(
            count=documentation_count,
            set_name=f"{set_name} - Documentation"
        )
        
        # Generate troubleshooting data
        troubleshooting_set = self.generate_troubleshooting_data(
            count=troubleshooting_count,
            set_name=f"{set_name} - Troubleshooting"
        )
        
        # Generate maintenance data
        maintenance_set = self.generate_maintenance_data(
            count=maintenance_count,
            set_name=f"{set_name} - Maintenance"
        )
        
        # Generate conversation data
        conversation_set = self.generate_conversation_data(
            count=conversation_count,
            set_name=f"{set_name} - Conversation"
        )
        
        # Generate reference data
        reference_set = self.generate_reference_data(
            set_name=f"{set_name} - Reference"
        )
        
        # Generate mock data
        mock_set = self.generate_mock_data(
            set_name=f"{set_name} - Mock"
        )
        
        return data_set


# Example usage
if __name__ == "__main__":
    # Create data manager
    manager = DataManager()
    
    # Create data generator
    generator = DataGenerator(data_manager=manager, seed=42)
    
    # Generate all data
    data_set = generator.generate_all_data(
        documentation_count=5,
        troubleshooting_count=5,
        maintenance_count=5,
        conversation_count=5
    )
    
    print(f"Generated data set: {data_set.name}")
    print(f"Total items: {sum(len(data_set.items) for data_set in manager.sets.values())}")
