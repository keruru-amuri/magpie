"""Configuration settings for MAGPIE platform."""

import os
from enum import Enum
from functools import lru_cache
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(str, Enum):
    """Environment types for the application."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class BaseAppSettings(BaseSettings):
    """Base settings class with common configuration."""

    # Environment
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT
    DEBUG: bool = False
    LOG_LEVEL: str = "info"

    # Base
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "MAGPIE"
    DESCRIPTION: str = "MAG Platform for Intelligent Execution - A multiagent LLM platform for aircraft MRO"
    VERSION: str = "0.1.0"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins from string or list."""
        import json

        if isinstance(v, str):
            # Handle comma-separated string
            if not v.startswith("["):
                return [i.strip() for i in v.split(",")]
            # Handle JSON string
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_VERSION: str = "2023-12-01-preview"

    # Model Deployment Names
    GPT_4_1_DEPLOYMENT_NAME: str = "gpt-4-1"
    GPT_4_1_MINI_DEPLOYMENT_NAME: str = "gpt-4-1-mini"
    GPT_4_1_NANO_DEPLOYMENT_NAME: str = "gpt-4-1-nano"

    # Database
    DATABASE_URL: Optional[str] = ""

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = ""

    # Task Master (for compatibility with existing .env)
    ANTHROPIC_API_KEY: Optional[str] = ""
    MODEL: Optional[str] = ""
    MAX_TOKENS: Optional[str] = ""
    TEMPERATURE: Optional[str] = ""
    DEFAULT_SUBTASKS: Optional[int] = 5
    DEFAULT_PRIORITY: Optional[str] = "medium"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env"
    )


class DevelopmentSettings(BaseAppSettings):
    """Development environment settings."""

    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT
    DEBUG: bool = True
    LOG_LEVEL: str = "debug"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


class TestingSettings(BaseAppSettings):
    """Testing environment settings."""

    ENVIRONMENT: EnvironmentType = EnvironmentType.TESTING
    DEBUG: bool = True
    LOG_LEVEL: str = "debug"
    TESTING: bool = True

    # Use in-memory SQLite for testing
    DATABASE_URL: str = "sqlite:///./test.db"

    # Use in-memory Redis for testing
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    model_config = SettingsConfigDict(
        env_file=".env.test",
        case_sensitive=True,
    )


class ProductionSettings(BaseAppSettings):
    """Production environment settings."""

    ENVIRONMENT: EnvironmentType = EnvironmentType.PRODUCTION
    DEBUG: bool = False
    LOG_LEVEL: str = "info"

    model_config = SettingsConfigDict(
        env_file=".env.prod",
        case_sensitive=True,
    )


@lru_cache()
def get_settings() -> BaseAppSettings:
    """
    Get the appropriate settings based on the environment.

    Uses environment variable ENVIRONMENT to determine which settings to load.
    Caches the result to avoid reloading settings on every call.
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()

    if environment == EnvironmentType.DEVELOPMENT.value:
        return DevelopmentSettings()
    elif environment == EnvironmentType.TESTING.value:
        return TestingSettings()
    elif environment == EnvironmentType.PRODUCTION.value:
        return ProductionSettings()
    else:
        # Default to development settings if environment is not recognized
        # Force the ENVIRONMENT to be development to avoid validation errors
        return DevelopmentSettings(ENVIRONMENT=EnvironmentType.DEVELOPMENT)


# Export the settings instance for use throughout the application
settings = get_settings()
