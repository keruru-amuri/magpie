"""Configuration for mock data infrastructure."""

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base path for mock data
MOCK_DATA_BASE_PATH = Path(__file__).parent.parent.parent.parent / "data" / "mock"


class MockDataSource(str, Enum):
    """Available mock data sources."""

    DOCUMENTATION = "documentation"
    TROUBLESHOOTING = "troubleshooting"
    MAINTENANCE = "maintenance"


class MockDataPaths(BaseModel):
    """Paths to mock data files."""

    base_path: Path = Field(default=MOCK_DATA_BASE_PATH)
    documentation_path: Path = Field(default_factory=lambda: MOCK_DATA_BASE_PATH / "documentation")
    troubleshooting_path: Path = Field(default_factory=lambda: MOCK_DATA_BASE_PATH / "troubleshooting")
    maintenance_path: Path = Field(default_factory=lambda: MOCK_DATA_BASE_PATH / "maintenance")
    schemas_path: Path = Field(default_factory=lambda: MOCK_DATA_BASE_PATH / "schemas")

    def get_path_for_source(self, source: MockDataSource) -> Path:
        """Get the path for a specific mock data source."""
        if source == MockDataSource.DOCUMENTATION:
            return self.documentation_path
        elif source == MockDataSource.TROUBLESHOOTING:
            return self.troubleshooting_path
        elif source == MockDataSource.MAINTENANCE:
            return self.maintenance_path
        else:
            raise ValueError(f"Unknown mock data source: {source}")


class MockDataConfig(BaseSettings):
    """Configuration for mock data infrastructure."""

    # Enable/disable mock data
    use_mock_data: bool = True
    
    # Paths to mock data
    paths: MockDataPaths = Field(default_factory=MockDataPaths)
    
    # Cache configuration
    enable_cache: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    
    # Schema validation
    validate_schemas: bool = True
    
    # Mock data generation
    enable_dynamic_generation: bool = False
    
    # Feature flags for specific mock data sources
    enable_documentation: bool = True
    enable_troubleshooting: bool = True
    enable_maintenance: bool = True
    
    # Performance simulation
    simulate_latency: bool = False
    min_latency_ms: int = 50
    max_latency_ms: int = 200
    
    model_config = SettingsConfigDict(
        env_prefix="MOCK_DATA_",
        case_sensitive=False,
    )
    
    def is_source_enabled(self, source: MockDataSource) -> bool:
        """Check if a specific mock data source is enabled."""
        if not self.use_mock_data:
            return False
            
        if source == MockDataSource.DOCUMENTATION:
            return self.enable_documentation
        elif source == MockDataSource.TROUBLESHOOTING:
            return self.enable_troubleshooting
        elif source == MockDataSource.MAINTENANCE:
            return self.enable_maintenance
        else:
            return False


@lru_cache()
def get_mock_data_config() -> MockDataConfig:
    """
    Get the mock data configuration.
    
    Uses environment variables with prefix MOCK_DATA_ to configure the mock data.
    Caches the result to avoid reloading configuration on every call.
    """
    return MockDataConfig()


# Export the configuration instance for use throughout the application
mock_data_config = get_mock_data_config()
