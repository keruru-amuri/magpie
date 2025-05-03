"""Configuration settings for MAGPIE platform."""

from typing import List, Optional, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

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
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
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

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env"
    )


settings = Settings()
