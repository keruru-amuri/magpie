"""
Utilities for resetting system state between tests.

This module provides utilities for resetting the system state between tests.
"""
import os
import logging
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path

from app.core.db.connection import Base
from app.core.cache.connection import RedisMockManager

# Configure logging
logger = logging.getLogger(__name__)


class SystemStateResetter:
    """
    Utility for resetting system state between tests.
    """
    
    def __init__(self):
        """Initialize the system state resetter."""
        self.reset_functions = []
    
    def add_reset_function(self, func: Callable):
        """
        Add a reset function.
        
        Args:
            func: Reset function
        """
        self.reset_functions.append(func)
    
    def reset_database(self, engine):
        """
        Reset database state.
        
        Args:
            engine: SQLAlchemy engine
        """
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database state reset")
    
    def reset_cache(self):
        """Reset cache state."""
        # Get fake Redis instance
        fake_redis = RedisMockManager.get_fake_redis()
        
        # Flush all keys
        fake_redis.flushall()
        
        logger.info("Cache state reset")
    
    def reset_filesystem(self, base_dir: Union[str, Path]):
        """
        Reset filesystem state.
        
        Args:
            base_dir: Base directory
        """
        # Create base directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)
        
        # Remove all files and directories
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        
        logger.info(f"Filesystem state reset: {base_dir}")
    
    def reset_all(self):
        """Reset all system state."""
        # Run all reset functions
        for func in self.reset_functions:
            try:
                func()
            except Exception as e:
                logger.warning(f"Error during reset: {str(e)}")
        
        logger.info("System state reset")


class DatabaseResetter:
    """
    Utility for resetting database state.
    """
    
    def __init__(self, engine):
        """
        Initialize the database resetter.
        
        Args:
            engine: SQLAlchemy engine
        """
        self.engine = engine
    
    def reset(self):
        """Reset database state."""
        # Drop all tables
        Base.metadata.drop_all(bind=self.engine)
        
        # Create all tables
        Base.metadata.create_all(bind=self.engine)
        
        logger.info("Database state reset")


class CacheResetter:
    """
    Utility for resetting cache state.
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize the cache resetter.
        
        Args:
            redis_client: Optional Redis client
        """
        self.redis_client = redis_client
    
    def reset(self):
        """Reset cache state."""
        if self.redis_client:
            # Flush all keys
            self.redis_client.flushall()
        else:
            # Get fake Redis instance
            fake_redis = RedisMockManager.get_fake_redis()
            
            # Flush all keys
            fake_redis.flushall()
        
        logger.info("Cache state reset")


class FilesystemResetter:
    """
    Utility for resetting filesystem state.
    """
    
    def __init__(self, base_dir: Union[str, Path]):
        """
        Initialize the filesystem resetter.
        
        Args:
            base_dir: Base directory
        """
        self.base_dir = Path(base_dir)
    
    def reset(self):
        """Reset filesystem state."""
        # Create base directory if it doesn't exist
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Remove all files and directories
        for item in os.listdir(self.base_dir):
            item_path = os.path.join(self.base_dir, item)
            
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        
        logger.info(f"Filesystem state reset: {self.base_dir}")


# Example usage
if __name__ == "__main__":
    # Create system state resetter
    resetter = SystemStateResetter()
    
    # Add reset functions
    resetter.add_reset_function(lambda: print("Resetting database"))
    resetter.add_reset_function(lambda: print("Resetting cache"))
    
    # Reset all system state
    resetter.reset_all()
