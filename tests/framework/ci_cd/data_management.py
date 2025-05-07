"""
Test data management for the MAGPIE platform.

This module provides utilities for managing test data.
"""
import os
import json
import shutil
import logging
import hashlib
from typing import Dict, List, Any, Optional, Union, Set
from enum import Enum
from datetime import datetime
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class DataCategory(Enum):
    """Enum for data categories."""
    DOCUMENTATION = "documentation"
    TROUBLESHOOTING = "troubleshooting"
    MAINTENANCE = "maintenance"
    CONVERSATION = "conversation"
    REFERENCE = "reference"
    MOCK = "mock"


class DataFormat(Enum):
    """Enum for data formats."""
    JSON = "json"
    CSV = "csv"
    TEXT = "text"
    BINARY = "binary"


class DataItem:
    """
    Model for data items.
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        category: DataCategory,
        format: DataFormat,
        path: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ):
        """
        Initialize data item.
        
        Args:
            id: Item ID
            name: Item name
            category: Data category
            format: Data format
            path: Item path
            metadata: Optional metadata
            tags: Optional tags
        """
        self.id = id
        self.name = name
        self.category = category
        self.format = format
        self.path = path
        self.metadata = metadata or {}
        self.tags = tags or []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """
        Calculate file checksum.
        
        Returns:
            File checksum
        """
        if not os.path.exists(self.path):
            return ""
        
        # Calculate MD5 checksum
        hash_md5 = hashlib.md5()
        
        with open(self.path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        
        return hash_md5.hexdigest()
    
    def update_checksum(self):
        """Update file checksum."""
        self.checksum = self._calculate_checksum()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "format": self.format.value,
            "path": self.path,
            "metadata": self.metadata,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "checksum": self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataItem':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Data item
        """
        item = cls(
            id=data["id"],
            name=data["name"],
            category=DataCategory(data["category"]),
            format=DataFormat(data["format"]),
            path=data["path"],
            metadata=data.get("metadata", {}),
            tags=data.get("tags", [])
        )
        
        item.created_at = datetime.fromisoformat(data["created_at"])
        item.updated_at = datetime.fromisoformat(data["updated_at"])
        item.checksum = data["checksum"]
        
        return item


class DataSet:
    """
    Model for data sets.
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ):
        """
        Initialize data set.
        
        Args:
            id: Set ID
            name: Set name
            description: Optional description
            metadata: Optional metadata
            tags: Optional tags
        """
        self.id = id
        self.name = name
        self.description = description or f"Data set: {name}"
        self.metadata = metadata or {}
        self.tags = tags or []
        self.items = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_item(self, item: DataItem):
        """
        Add a data item.
        
        Args:
            item: Data item
        """
        self.items[item.id] = item
        self.updated_at = datetime.now()
    
    def remove_item(self, item_id: str) -> bool:
        """
        Remove a data item.
        
        Args:
            item_id: Item ID
            
        Returns:
            True if removed, False otherwise
        """
        if item_id in self.items:
            del self.items[item_id]
            self.updated_at = datetime.now()
            return True
        
        return False
    
    def get_item(self, item_id: str) -> Optional[DataItem]:
        """
        Get a data item.
        
        Args:
            item_id: Item ID
            
        Returns:
            Data item or None if not found
        """
        return self.items.get(item_id)
    
    def get_items_by_category(self, category: DataCategory) -> List[DataItem]:
        """
        Get data items by category.
        
        Args:
            category: Data category
            
        Returns:
            List of data items
        """
        return [
            item for item in self.items.values()
            if item.category == category
        ]
    
    def get_items_by_tag(self, tag: str) -> List[DataItem]:
        """
        Get data items by tag.
        
        Args:
            tag: Tag
            
        Returns:
            List of data items
        """
        return [
            item for item in self.items.values()
            if tag in item.tags
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "metadata": self.metadata,
            "tags": self.tags,
            "items": {item_id: item.to_dict() for item_id, item in self.items.items()},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataSet':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Data set
        """
        data_set = cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", [])
        )
        
        data_set.created_at = datetime.fromisoformat(data["created_at"])
        data_set.updated_at = datetime.fromisoformat(data["updated_at"])
        
        for item_id, item_data in data["items"].items():
            data_set.items[item_id] = DataItem.from_dict(item_data)
        
        return data_set


class DataManager:
    """
    Manager for test data.
    """
    
    def __init__(
        self,
        data_dir: Optional[Union[str, Path]] = None,
        catalog_file: Optional[Union[str, Path]] = None
    ):
        """
        Initialize data manager.
        
        Args:
            data_dir: Optional data directory
            catalog_file: Optional catalog file
        """
        self.data_dir = data_dir or Path("test_data")
        self.catalog_file = catalog_file or Path(self.data_dir) / "catalog.json"
        self.sets = {}
        
        # Create data directory
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load catalog
        self._load_catalog()
    
    def _load_catalog(self):
        """Load data catalog."""
        if not os.path.exists(self.catalog_file):
            return
        
        try:
            with open(self.catalog_file, "r") as f:
                catalog = json.load(f)
            
            for set_id, set_data in catalog.get("sets", {}).items():
                self.sets[set_id] = DataSet.from_dict(set_data)
            
            logger.info(f"Loaded {len(self.sets)} data sets from catalog")
        except Exception as e:
            logger.warning(f"Error loading data catalog: {str(e)}")
    
    def _save_catalog(self):
        """Save data catalog."""
        try:
            catalog = {
                "sets": {set_id: data_set.to_dict() for set_id, data_set in self.sets.items()}
            }
            
            with open(self.catalog_file, "w") as f:
                json.dump(catalog, f, indent=2)
            
            logger.info(f"Saved {len(self.sets)} data sets to catalog")
        except Exception as e:
            logger.warning(f"Error saving data catalog: {str(e)}")
    
    def create_set(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> DataSet:
        """
        Create a data set.
        
        Args:
            name: Set name
            description: Optional description
            metadata: Optional metadata
            tags: Optional tags
            
        Returns:
            Data set
        """
        # Generate ID
        set_id = hashlib.md5(f"{name}_{datetime.now().isoformat()}".encode()).hexdigest()
        
        # Create set
        data_set = DataSet(
            id=set_id,
            name=name,
            description=description,
            metadata=metadata,
            tags=tags
        )
        
        # Add to sets
        self.sets[set_id] = data_set
        
        # Save catalog
        self._save_catalog()
        
        return data_set
    
    def get_set(self, set_id: str) -> Optional[DataSet]:
        """
        Get a data set.
        
        Args:
            set_id: Set ID
            
        Returns:
            Data set or None if not found
        """
        return self.sets.get(set_id)
    
    def get_set_by_name(self, name: str) -> Optional[DataSet]:
        """
        Get a data set by name.
        
        Args:
            name: Set name
            
        Returns:
            Data set or None if not found
        """
        for data_set in self.sets.values():
            if data_set.name == name:
                return data_set
        
        return None
    
    def remove_set(self, set_id: str) -> bool:
        """
        Remove a data set.
        
        Args:
            set_id: Set ID
            
        Returns:
            True if removed, False otherwise
        """
        if set_id in self.sets:
            del self.sets[set_id]
            self._save_catalog()
            return True
        
        return False
    
    def add_item(
        self,
        set_id: str,
        name: str,
        category: DataCategory,
        format: DataFormat,
        source_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[DataItem]:
        """
        Add a data item.
        
        Args:
            set_id: Set ID
            name: Item name
            category: Data category
            format: Data format
            source_path: Source path
            metadata: Optional metadata
            tags: Optional tags
            
        Returns:
            Data item or None if set not found
        """
        # Get set
        data_set = self.get_set(set_id)
        if not data_set:
            return None
        
        # Generate ID
        item_id = hashlib.md5(f"{name}_{datetime.now().isoformat()}".encode()).hexdigest()
        
        # Create category directory
        category_dir = Path(self.data_dir) / set_id / category.value
        os.makedirs(category_dir, exist_ok=True)
        
        # Determine target path
        extension = format.value
        if format == DataFormat.JSON:
            extension = "json"
        elif format == DataFormat.CSV:
            extension = "csv"
        elif format == DataFormat.TEXT:
            extension = "txt"
        elif format == DataFormat.BINARY:
            extension = "bin"
        
        target_path = category_dir / f"{item_id}.{extension}"
        
        # Copy file
        try:
            shutil.copy2(source_path, target_path)
        except Exception as e:
            logger.warning(f"Error copying file: {str(e)}")
            return None
        
        # Create item
        item = DataItem(
            id=item_id,
            name=name,
            category=category,
            format=format,
            path=str(target_path),
            metadata=metadata,
            tags=tags
        )
        
        # Add to set
        data_set.add_item(item)
        
        # Save catalog
        self._save_catalog()
        
        return item
    
    def remove_item(self, set_id: str, item_id: str) -> bool:
        """
        Remove a data item.
        
        Args:
            set_id: Set ID
            item_id: Item ID
            
        Returns:
            True if removed, False otherwise
        """
        # Get set
        data_set = self.get_set(set_id)
        if not data_set:
            return False
        
        # Get item
        item = data_set.get_item(item_id)
        if not item:
            return False
        
        # Remove file
        try:
            os.remove(item.path)
        except Exception as e:
            logger.warning(f"Error removing file: {str(e)}")
        
        # Remove from set
        data_set.remove_item(item_id)
        
        # Save catalog
        self._save_catalog()
        
        return True
    
    def get_item(self, set_id: str, item_id: str) -> Optional[DataItem]:
        """
        Get a data item.
        
        Args:
            set_id: Set ID
            item_id: Item ID
            
        Returns:
            Data item or None if not found
        """
        # Get set
        data_set = self.get_set(set_id)
        if not data_set:
            return None
        
        # Get item
        return data_set.get_item(item_id)
    
    def get_items_by_category(
        self,
        category: DataCategory,
        set_id: Optional[str] = None
    ) -> List[DataItem]:
        """
        Get data items by category.
        
        Args:
            category: Data category
            set_id: Optional set ID
            
        Returns:
            List of data items
        """
        items = []
        
        if set_id:
            # Get items from specific set
            data_set = self.get_set(set_id)
            if data_set:
                items.extend(data_set.get_items_by_category(category))
        else:
            # Get items from all sets
            for data_set in self.sets.values():
                items.extend(data_set.get_items_by_category(category))
        
        return items
    
    def get_items_by_tag(
        self,
        tag: str,
        set_id: Optional[str] = None
    ) -> List[DataItem]:
        """
        Get data items by tag.
        
        Args:
            tag: Tag
            set_id: Optional set ID
            
        Returns:
            List of data items
        """
        items = []
        
        if set_id:
            # Get items from specific set
            data_set = self.get_set(set_id)
            if data_set:
                items.extend(data_set.get_items_by_tag(tag))
        else:
            # Get items from all sets
            for data_set in self.sets.values():
                items.extend(data_set.get_items_by_tag(tag))
        
        return items
    
    def update_checksums(self):
        """Update checksums for all data items."""
        for data_set in self.sets.values():
            for item in data_set.items.values():
                item.update_checksum()
        
        # Save catalog
        self._save_catalog()
    
    def verify_checksums(self) -> Dict[str, List[str]]:
        """
        Verify checksums for all data items.
        
        Returns:
            Dictionary of set IDs to list of invalid item IDs
        """
        invalid_items = {}
        
        for set_id, data_set in self.sets.items():
            invalid_set_items = []
            
            for item_id, item in data_set.items.items():
                # Calculate current checksum
                current_checksum = item._calculate_checksum()
                
                # Compare with stored checksum
                if current_checksum != item.checksum:
                    invalid_set_items.append(item_id)
            
            if invalid_set_items:
                invalid_items[set_id] = invalid_set_items
        
        return invalid_items
    
    def export_set(
        self,
        set_id: str,
        target_dir: Union[str, Path]
    ) -> bool:
        """
        Export a data set.
        
        Args:
            set_id: Set ID
            target_dir: Target directory
            
        Returns:
            True if exported, False otherwise
        """
        # Get set
        data_set = self.get_set(set_id)
        if not data_set:
            return False
        
        # Create target directory
        os.makedirs(target_dir, exist_ok=True)
        
        # Export set metadata
        set_metadata = data_set.to_dict()
        
        with open(Path(target_dir) / "metadata.json", "w") as f:
            json.dump(set_metadata, f, indent=2)
        
        # Export items
        for item_id, item in data_set.items.items():
            # Create category directory
            category_dir = Path(target_dir) / item.category.value
            os.makedirs(category_dir, exist_ok=True)
            
            # Copy file
            try:
                shutil.copy2(item.path, category_dir / os.path.basename(item.path))
            except Exception as e:
                logger.warning(f"Error copying file: {str(e)}")
        
        return True
    
    def import_set(
        self,
        source_dir: Union[str, Path]
    ) -> Optional[DataSet]:
        """
        Import a data set.
        
        Args:
            source_dir: Source directory
            
        Returns:
            Data set or None if import failed
        """
        # Check metadata file
        metadata_file = Path(source_dir) / "metadata.json"
        if not os.path.exists(metadata_file):
            logger.warning(f"Metadata file not found: {metadata_file}")
            return None
        
        try:
            # Load metadata
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            
            # Create set
            data_set = self.create_set(
                name=metadata["name"],
                description=metadata.get("description"),
                metadata=metadata.get("metadata", {}),
                tags=metadata.get("tags", [])
            )
            
            # Import items
            for item_id, item_data in metadata["items"].items():
                # Get source path
                source_path = Path(source_dir) / item_data["category"] / os.path.basename(item_data["path"])
                
                if not os.path.exists(source_path):
                    logger.warning(f"Item file not found: {source_path}")
                    continue
                
                # Add item
                self.add_item(
                    set_id=data_set.id,
                    name=item_data["name"],
                    category=DataCategory(item_data["category"]),
                    format=DataFormat(item_data["format"]),
                    source_path=str(source_path),
                    metadata=item_data.get("metadata", {}),
                    tags=item_data.get("tags", [])
                )
            
            return data_set
        except Exception as e:
            logger.warning(f"Error importing data set: {str(e)}")
            return None


# Example usage
if __name__ == "__main__":
    # Create data manager
    manager = DataManager()
    
    # Create data set
    data_set = manager.create_set(
        name="Aircraft Maintenance",
        description="Test data for aircraft maintenance",
        tags=["maintenance", "test"]
    )
    
    # Add items
    manager.add_item(
        set_id=data_set.id,
        name="Boeing 737 Maintenance Manual",
        category=DataCategory.DOCUMENTATION,
        format=DataFormat.TEXT,
        source_path="path/to/manual.txt",
        tags=["boeing", "737", "manual"]
    )
    
    manager.add_item(
        set_id=data_set.id,
        name="Tire Pressure Reference",
        category=DataCategory.REFERENCE,
        format=DataFormat.JSON,
        source_path="path/to/tire_pressure.json",
        tags=["tire", "pressure", "reference"]
    )
    
    # Get items by category
    documentation_items = manager.get_items_by_category(DataCategory.DOCUMENTATION)
    print(f"Documentation items: {len(documentation_items)}")
    
    # Get items by tag
    tire_items = manager.get_items_by_tag("tire")
    print(f"Tire items: {len(tire_items)}")
    
    # Update checksums
    manager.update_checksums()
    
    # Verify checksums
    invalid_items = manager.verify_checksums()
    print(f"Invalid items: {invalid_items}")
    
    # Export set
    manager.export_set(data_set.id, "path/to/export")
    
    # Import set
    imported_set = manager.import_set("path/to/export")
    print(f"Imported set: {imported_set.name if imported_set else None}")
