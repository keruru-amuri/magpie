"""
Integration test environment configuration.

This module provides utilities for configuring integration test environments.
"""
import os
import json
import logging
import tempfile
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
from pathlib import Path

from app.core.config import settings
from app.core.db.connection import get_db, get_async_db
from app.core.cache.connection import get_redis, get_async_redis

# Configure logging
logger = logging.getLogger(__name__)


class DependencyType(Enum):
    """Enum for dependency types."""
    DATABASE = "database"
    CACHE = "cache"
    LLM = "llm"
    DOCUMENTATION = "documentation"
    TROUBLESHOOTING = "troubleshooting"
    MAINTENANCE = "maintenance"
    MOCK_DATA = "mock_data"
    FILESYSTEM = "filesystem"


class DependencyMode(Enum):
    """Enum for dependency modes."""
    REAL = "real"
    MOCK = "mock"
    HYBRID = "hybrid"


class IntegrationTestEnvironment:
    """
    Integration test environment configuration.
    
    This class provides utilities for configuring integration test environments
    with either real or mock dependencies.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the integration test environment.
        
        Args:
            config_path: Optional path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize dependencies
        self.dependencies = {}
        self.cleanup_functions = []
        
        # Set up temporary directory for test artifacts
        self.temp_dir = tempfile.TemporaryDirectory()
        self.artifacts_dir = Path(self.temp_dir.name)
        
        # Initialize environment
        self._initialize_environment()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Optional path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "dependencies": {
                DependencyType.DATABASE.value: DependencyMode.MOCK.value,
                DependencyType.CACHE.value: DependencyMode.MOCK.value,
                DependencyType.LLM.value: DependencyMode.MOCK.value,
                DependencyType.DOCUMENTATION.value: DependencyMode.MOCK.value,
                DependencyType.TROUBLESHOOTING.value: DependencyMode.MOCK.value,
                DependencyType.MAINTENANCE.value: DependencyMode.MOCK.value,
                DependencyType.MOCK_DATA.value: DependencyMode.REAL.value,
                DependencyType.FILESYSTEM.value: DependencyMode.MOCK.value
            },
            "mock_data": {
                "use_mock_data": True,
                "validate_schemas": True,
                "enable_cache": False
            },
            "database": {
                "use_in_memory": True,
                "create_tables": True
            },
            "cache": {
                "use_fake_redis": True
            },
            "llm": {
                "use_mock_responses": True,
                "response_template": "This is a mock response for: {query}"
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    user_config = json.load(f)
                
                # Merge user config with defaults
                for key, value in user_config.items():
                    if key in default_config and isinstance(value, dict):
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
            except Exception as e:
                logger.warning(f"Error loading config from {config_path}: {str(e)}")
        
        return default_config
    
    def _initialize_environment(self):
        """Initialize the test environment."""
        # Set up database
        self._setup_database()
        
        # Set up cache
        self._setup_cache()
        
        # Set up LLM
        self._setup_llm()
        
        # Set up mock data
        self._setup_mock_data()
        
        # Set up filesystem
        self._setup_filesystem()
        
        # Set up service dependencies
        self._setup_service_dependencies()
        
        logger.info("Integration test environment initialized")
    
    def _setup_database(self):
        """Set up database dependency."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from app.core.db.connection import Base
        
        if self.config["dependencies"][DependencyType.DATABASE.value] == DependencyMode.MOCK.value:
            # Use in-memory SQLite database
            if self.config["database"]["use_in_memory"]:
                engine = create_engine(
                    "sqlite:///:memory:",
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=False
                )
            else:
                # Use file-based SQLite database
                db_path = self.artifacts_dir / "test.db"
                engine = create_engine(
                    f"sqlite:///{db_path}",
                    connect_args={"check_same_thread": False},
                    echo=False
                )
            
            # Create session factory
            TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            # Create tables
            if self.config["database"]["create_tables"]:
                Base.metadata.create_all(bind=engine)
            
            # Store dependencies
            self.dependencies[DependencyType.DATABASE.value] = {
                "engine": engine,
                "session_factory": TestingSessionLocal
            }
            
            # Add cleanup function
            def cleanup_database():
                if not self.config["database"]["use_in_memory"]:
                    try:
                        os.remove(self.artifacts_dir / "test.db")
                    except:
                        pass
            
            self.cleanup_functions.append(cleanup_database)
            
            logger.info("Mock database initialized")
        else:
            # Use real database
            self.dependencies[DependencyType.DATABASE.value] = {
                "get_db": get_db,
                "get_async_db": get_async_db
            }
            
            logger.info("Real database connection initialized")
    
    def _setup_cache(self):
        """Set up cache dependency."""
        if self.config["dependencies"][DependencyType.CACHE.value] == DependencyMode.MOCK.value:
            from app.core.cache.connection import RedisMockManager
            
            # Enable Redis mock
            RedisMockManager.enable_redis_mock()
            
            # Get fake Redis instance
            fake_redis = RedisMockManager.get_fake_redis()
            
            # Store dependencies
            self.dependencies[DependencyType.CACHE.value] = {
                "redis": fake_redis
            }
            
            # Add cleanup function
            def cleanup_cache():
                RedisMockManager.disable_redis_mock()
            
            self.cleanup_functions.append(cleanup_cache)
            
            logger.info("Mock cache initialized")
        else:
            # Use real Redis
            self.dependencies[DependencyType.CACHE.value] = {
                "get_redis": get_redis,
                "get_async_redis": get_async_redis
            }
            
            logger.info("Real cache connection initialized")
    
    def _setup_llm(self):
        """Set up LLM dependency."""
        if self.config["dependencies"][DependencyType.LLM.value] == DependencyMode.MOCK.value:
            from tests.framework.fixtures.agent_fixtures import MockLLMService
            
            # Create mock LLM service
            mock_llm_service = MockLLMService(
                response_template=self.config["llm"]["response_template"]
            )
            
            # Store dependencies
            self.dependencies[DependencyType.LLM.value] = {
                "llm_service": mock_llm_service
            }
            
            logger.info("Mock LLM service initialized")
        else:
            # Use real LLM service
            from app.services.llm_service import LLMService
            
            llm_service = LLMService()
            
            # Store dependencies
            self.dependencies[DependencyType.LLM.value] = {
                "llm_service": llm_service
            }
            
            logger.info("Real LLM service initialized")
    
    def _setup_mock_data(self):
        """Set up mock data dependency."""
        if self.config["dependencies"][DependencyType.MOCK_DATA.value] == DependencyMode.REAL.value:
            from app.core.mock.config import MockDataConfig
            from app.core.mock.loader import MockDataLoader
            from app.core.mock.service import MockDataService
            
            # Create mock data configuration
            mock_data_config = MockDataConfig(
                use_mock_data=self.config["mock_data"]["use_mock_data"],
                validate_schemas=self.config["mock_data"]["validate_schemas"],
                enable_cache=self.config["mock_data"]["enable_cache"]
            )
            
            # Create mock data loader
            mock_data_loader = MockDataLoader(config=mock_data_config)
            
            # Create mock data service
            mock_data_service = MockDataService(
                config=mock_data_config,
                loader=mock_data_loader
            )
            
            # Store dependencies
            self.dependencies[DependencyType.MOCK_DATA.value] = {
                "config": mock_data_config,
                "loader": mock_data_loader,
                "service": mock_data_service
            }
            
            logger.info("Mock data service initialized")
        else:
            # Use custom mock data
            logger.info("Custom mock data not implemented")
    
    def _setup_filesystem(self):
        """Set up filesystem dependency."""
        if self.config["dependencies"][DependencyType.FILESYSTEM.value] == DependencyMode.MOCK.value:
            # Create temporary directories for file operations
            for dir_name in ["documents", "exports", "uploads", "logs"]:
                os.makedirs(self.artifacts_dir / dir_name, exist_ok=True)
            
            # Store dependencies
            self.dependencies[DependencyType.FILESYSTEM.value] = {
                "base_dir": self.artifacts_dir,
                "documents_dir": self.artifacts_dir / "documents",
                "exports_dir": self.artifacts_dir / "exports",
                "uploads_dir": self.artifacts_dir / "uploads",
                "logs_dir": self.artifacts_dir / "logs"
            }
            
            logger.info("Mock filesystem initialized")
        else:
            # Use real filesystem
            base_dir = Path(settings.BASE_DIR)
            
            # Store dependencies
            self.dependencies[DependencyType.FILESYSTEM.value] = {
                "base_dir": base_dir,
                "documents_dir": base_dir / "documents",
                "exports_dir": base_dir / "exports",
                "uploads_dir": base_dir / "uploads",
                "logs_dir": base_dir / "logs"
            }
            
            logger.info("Real filesystem initialized")
    
    def _setup_service_dependencies(self):
        """Set up service dependencies."""
        # Documentation service
        if self.config["dependencies"][DependencyType.DOCUMENTATION.value] == DependencyMode.MOCK.value:
            from tests.framework.fixtures.agent_fixtures import MockDocumentationService
            
            # Create mock documentation service
            mock_documentation_service = MockDocumentationService()
            
            # Store dependencies
            self.dependencies[DependencyType.DOCUMENTATION.value] = {
                "documentation_service": mock_documentation_service
            }
            
            logger.info("Mock documentation service initialized")
        
        # Troubleshooting service
        if self.config["dependencies"][DependencyType.TROUBLESHOOTING.value] == DependencyMode.MOCK.value:
            from tests.framework.fixtures.agent_fixtures import MockTroubleshootingService
            
            # Create mock troubleshooting service
            mock_troubleshooting_service = MockTroubleshootingService()
            
            # Store dependencies
            self.dependencies[DependencyType.TROUBLESHOOTING.value] = {
                "troubleshooting_service": mock_troubleshooting_service
            }
            
            logger.info("Mock troubleshooting service initialized")
        
        # Maintenance service
        if self.config["dependencies"][DependencyType.MAINTENANCE.value] == DependencyMode.MOCK.value:
            from tests.framework.fixtures.agent_fixtures import MockMaintenanceService
            
            # Create mock maintenance service
            mock_maintenance_service = MockMaintenanceService()
            
            # Store dependencies
            self.dependencies[DependencyType.MAINTENANCE.value] = {
                "maintenance_service": mock_maintenance_service
            }
            
            logger.info("Mock maintenance service initialized")
    
    def get_dependency(self, dependency_type: Union[DependencyType, str]) -> Dict[str, Any]:
        """
        Get dependency by type.
        
        Args:
            dependency_type: Dependency type
            
        Returns:
            Dependency dictionary
        """
        if isinstance(dependency_type, DependencyType):
            dependency_type = dependency_type.value
        
        return self.dependencies.get(dependency_type, {})
    
    def cleanup(self):
        """Clean up the test environment."""
        # Run cleanup functions
        for cleanup_func in self.cleanup_functions:
            try:
                cleanup_func()
            except Exception as e:
                logger.warning(f"Error during cleanup: {str(e)}")
        
        # Clean up temporary directory
        self.temp_dir.cleanup()
        
        logger.info("Integration test environment cleaned up")


# Example usage
if __name__ == "__main__":
    # Create integration test environment
    env = IntegrationTestEnvironment()
    
    # Get database dependency
    db_dependency = env.get_dependency(DependencyType.DATABASE)
    
    # Get LLM dependency
    llm_dependency = env.get_dependency(DependencyType.LLM)
    
    # Clean up
    env.cleanup()
