"""
Reference dataset for response quality evaluation.

This module provides utilities for creating and managing reference datasets
for response quality evaluation.
"""
import os
import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Union, Set
from enum import Enum
from datetime import datetime
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class ReferenceType(Enum):
    """Enum for reference types."""
    QUERY_RESPONSE = "query_response"
    FACT = "fact"
    REQUIRED_ELEMENT = "required_element"
    UNSAFE_PATTERN = "unsafe_pattern"


class ReferenceItem:
    """
    Model for reference items.
    """
    
    def __init__(
        self,
        id: str,
        type: ReferenceType,
        content: Dict[str, Any],
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a reference item.
        
        Args:
            id: Item ID
            type: Reference type
            content: Item content
            tags: Optional tags
            metadata: Optional metadata
        """
        self.id = id
        self.type = type
        self.content = content
        self.tags = tags or []
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReferenceItem':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Reference item
        """
        item = cls(
            id=data["id"],
            type=ReferenceType(data["type"]),
            content=data["content"],
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )
        
        item.created_at = datetime.fromisoformat(data["created_at"])
        item.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return item


class ReferenceDataset:
    """
    Dataset of reference items for response quality evaluation.
    """
    
    def __init__(self, name: str, description: Optional[str] = None):
        """
        Initialize a reference dataset.
        
        Args:
            name: Dataset name
            description: Optional description
        """
        self.name = name
        self.description = description or f"Reference dataset: {name}"
        self.items = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_item(self, item: ReferenceItem) -> str:
        """
        Add a reference item.
        
        Args:
            item: Reference item
            
        Returns:
            Item ID
        """
        self.items[item.id] = item
        self.updated_at = datetime.now()
        
        return item.id
    
    def get_item(self, id: str) -> Optional[ReferenceItem]:
        """
        Get a reference item by ID.
        
        Args:
            id: Item ID
            
        Returns:
            Reference item or None if not found
        """
        return self.items.get(id)
    
    def remove_item(self, id: str) -> bool:
        """
        Remove a reference item.
        
        Args:
            id: Item ID
            
        Returns:
            True if removed, False otherwise
        """
        if id in self.items:
            del self.items[id]
            self.updated_at = datetime.now()
            return True
        
        return False
    
    def get_items_by_type(self, type: ReferenceType) -> List[ReferenceItem]:
        """
        Get reference items by type.
        
        Args:
            type: Reference type
            
        Returns:
            List of reference items
        """
        return [item for item in self.items.values() if item.type == type]
    
    def get_items_by_tag(self, tag: str) -> List[ReferenceItem]:
        """
        Get reference items by tag.
        
        Args:
            tag: Tag
            
        Returns:
            List of reference items
        """
        return [item for item in self.items.values() if tag in item.tags]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "description": self.description,
            "items": {id: item.to_dict() for id, item in self.items.items()},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReferenceDataset':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Reference dataset
        """
        dataset = cls(
            name=data["name"],
            description=data.get("description")
        )
        
        dataset.created_at = datetime.fromisoformat(data["created_at"])
        dataset.updated_at = datetime.fromisoformat(data["updated_at"])
        
        for id, item_data in data["items"].items():
            dataset.items[id] = ReferenceItem.from_dict(item_data)
        
        return dataset
    
    def save(self, file_path: Union[str, Path]):
        """
        Save to file.
        
        Args:
            file_path: File path
        """
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, file_path: Union[str, Path]) -> 'ReferenceDataset':
        """
        Load from file.
        
        Args:
            file_path: File path
            
        Returns:
            Reference dataset
        """
        with open(file_path, "r") as f:
            data = json.load(f)
        
        return cls.from_dict(data)


class ReferenceDatasetManager:
    """
    Manager for reference datasets.
    """
    
    def __init__(self, data_dir: Optional[Union[str, Path]] = None):
        """
        Initialize a reference dataset manager.
        
        Args:
            data_dir: Optional data directory
        """
        self.data_dir = data_dir or Path("reference_data")
        
        # Create data directory
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load datasets
        self.datasets = {}
        self._load_datasets()
    
    def _load_datasets(self):
        """Load datasets from data directory."""
        for file_path in Path(self.data_dir).glob("*.json"):
            try:
                dataset = ReferenceDataset.load(file_path)
                self.datasets[dataset.name] = dataset
                logger.info(f"Loaded dataset: {dataset.name}")
            except Exception as e:
                logger.warning(f"Error loading dataset from {file_path}: {str(e)}")
    
    def create_dataset(self, name: str, description: Optional[str] = None) -> ReferenceDataset:
        """
        Create a new dataset.
        
        Args:
            name: Dataset name
            description: Optional description
            
        Returns:
            Reference dataset
        """
        if name in self.datasets:
            raise ValueError(f"Dataset already exists: {name}")
        
        dataset = ReferenceDataset(name, description)
        self.datasets[name] = dataset
        
        # Save dataset
        file_path = Path(self.data_dir) / f"{name}.json"
        dataset.save(file_path)
        
        logger.info(f"Created dataset: {name}")
        
        return dataset
    
    def get_dataset(self, name: str) -> Optional[ReferenceDataset]:
        """
        Get a dataset by name.
        
        Args:
            name: Dataset name
            
        Returns:
            Reference dataset or None if not found
        """
        return self.datasets.get(name)
    
    def remove_dataset(self, name: str) -> bool:
        """
        Remove a dataset.
        
        Args:
            name: Dataset name
            
        Returns:
            True if removed, False otherwise
        """
        if name in self.datasets:
            del self.datasets[name]
            
            # Remove file
            file_path = Path(self.data_dir) / f"{name}.json"
            if file_path.exists():
                os.remove(file_path)
            
            logger.info(f"Removed dataset: {name}")
            
            return True
        
        return False
    
    def save_dataset(self, name: str) -> bool:
        """
        Save a dataset to file.
        
        Args:
            name: Dataset name
            
        Returns:
            True if saved, False otherwise
        """
        if name in self.datasets:
            dataset = self.datasets[name]
            
            # Save dataset
            file_path = Path(self.data_dir) / f"{name}.json"
            dataset.save(file_path)
            
            logger.info(f"Saved dataset: {name}")
            
            return True
        
        return False
    
    def list_datasets(self) -> List[str]:
        """
        List all datasets.
        
        Returns:
            List of dataset names
        """
        return list(self.datasets.keys())
    
    def add_query_response(
        self,
        dataset_name: str,
        query: str,
        response: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Add a query-response pair to a dataset.
        
        Args:
            dataset_name: Dataset name
            query: Query
            response: Response
            tags: Optional tags
            metadata: Optional metadata
            
        Returns:
            Item ID or None if dataset not found
        """
        dataset = self.get_dataset(dataset_name)
        if not dataset:
            return None
        
        # Create reference item
        item = ReferenceItem(
            id=str(uuid.uuid4()),
            type=ReferenceType.QUERY_RESPONSE,
            content={
                "query": query,
                "response": response
            },
            tags=tags,
            metadata=metadata
        )
        
        # Add item to dataset
        item_id = dataset.add_item(item)
        
        # Save dataset
        self.save_dataset(dataset_name)
        
        return item_id
    
    def add_fact(
        self,
        dataset_name: str,
        key: str,
        value: Any,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Add a fact to a dataset.
        
        Args:
            dataset_name: Dataset name
            key: Fact key
            value: Fact value
            tags: Optional tags
            metadata: Optional metadata
            
        Returns:
            Item ID or None if dataset not found
        """
        dataset = self.get_dataset(dataset_name)
        if not dataset:
            return None
        
        # Create reference item
        item = ReferenceItem(
            id=str(uuid.uuid4()),
            type=ReferenceType.FACT,
            content={
                "key": key,
                "value": value
            },
            tags=tags,
            metadata=metadata
        )
        
        # Add item to dataset
        item_id = dataset.add_item(item)
        
        # Save dataset
        self.save_dataset(dataset_name)
        
        return item_id
    
    def add_required_element(
        self,
        dataset_name: str,
        element: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Add a required element to a dataset.
        
        Args:
            dataset_name: Dataset name
            element: Required element
            tags: Optional tags
            metadata: Optional metadata
            
        Returns:
            Item ID or None if dataset not found
        """
        dataset = self.get_dataset(dataset_name)
        if not dataset:
            return None
        
        # Create reference item
        item = ReferenceItem(
            id=str(uuid.uuid4()),
            type=ReferenceType.REQUIRED_ELEMENT,
            content={
                "element": element
            },
            tags=tags,
            metadata=metadata
        )
        
        # Add item to dataset
        item_id = dataset.add_item(item)
        
        # Save dataset
        self.save_dataset(dataset_name)
        
        return item_id
    
    def add_unsafe_pattern(
        self,
        dataset_name: str,
        pattern: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Add an unsafe pattern to a dataset.
        
        Args:
            dataset_name: Dataset name
            pattern: Unsafe pattern
            tags: Optional tags
            metadata: Optional metadata
            
        Returns:
            Item ID or None if dataset not found
        """
        dataset = self.get_dataset(dataset_name)
        if not dataset:
            return None
        
        # Create reference item
        item = ReferenceItem(
            id=str(uuid.uuid4()),
            type=ReferenceType.UNSAFE_PATTERN,
            content={
                "pattern": pattern
            },
            tags=tags,
            metadata=metadata
        )
        
        # Add item to dataset
        item_id = dataset.add_item(item)
        
        # Save dataset
        self.save_dataset(dataset_name)
        
        return item_id
    
    def get_reference_data(
        self,
        dataset_name: str,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get reference data for quality evaluation.
        
        Args:
            dataset_name: Dataset name
            tags: Optional tags filter
            
        Returns:
            Reference data
        """
        dataset = self.get_dataset(dataset_name)
        if not dataset:
            return {}
        
        # Initialize reference data
        reference_data = {
            "facts": {},
            "required_elements": [],
            "unsafe_patterns": []
        }
        
        # Filter items by tags
        items = dataset.items.values()
        if tags:
            items = [item for item in items if any(tag in item.tags for tag in tags)]
        
        # Process items
        for item in items:
            if item.type == ReferenceType.FACT:
                reference_data["facts"][item.content["key"]] = item.content["value"]
            elif item.type == ReferenceType.REQUIRED_ELEMENT:
                reference_data["required_elements"].append(item.content["element"])
            elif item.type == ReferenceType.UNSAFE_PATTERN:
                reference_data["unsafe_patterns"].append(item.content["pattern"])
            elif item.type == ReferenceType.QUERY_RESPONSE:
                # Add first query-response pair as reference
                if "reference_query" not in reference_data:
                    reference_data["reference_query"] = item.content["query"]
                    reference_data["reference_response"] = item.content["response"]
        
        return reference_data


# Example usage
if __name__ == "__main__":
    # Create manager
    manager = ReferenceDatasetManager()
    
    # Create dataset
    dataset = manager.create_dataset("aircraft_maintenance")
    
    # Add items
    manager.add_fact("aircraft_maintenance", "main_gear_pressure", "200 psi", tags=["tire", "pressure"])
    manager.add_fact("aircraft_maintenance", "nose_gear_pressure", "180 psi", tags=["tire", "pressure"])
    
    manager.add_required_element("aircraft_maintenance", "tire pressure", tags=["tire"])
    manager.add_required_element("aircraft_maintenance", "main landing gear", tags=["tire"])
    manager.add_required_element("aircraft_maintenance", "nose landing gear", tags=["tire"])
    manager.add_required_element("aircraft_maintenance", "maintenance manual", tags=["documentation"])
    
    manager.add_query_response(
        "aircraft_maintenance",
        "What is the recommended tire pressure for a Boeing 737?",
        """
        The recommended tire pressure for a Boeing 737-800 is 200 psi for the main landing gear
        and 180 psi for the nose landing gear. These values may vary slightly based on the specific
        aircraft configuration and operating conditions.
        
        Always refer to the Aircraft Maintenance Manual (AMM) for the exact specifications for your
        aircraft. The tire pressure should be checked daily as part of the pre-flight inspection.
        """,
        tags=["tire", "pressure"]
    )
    
    # Get reference data
    reference_data = manager.get_reference_data("aircraft_maintenance", tags=["tire"])
    
    # Print reference data
    print(f"Facts: {reference_data['facts']}")
    print(f"Required elements: {reference_data['required_elements']}")
