"""Tests for the configuration module."""

import os
from unittest import mock

import pytest
from pydantic import ValidationError

from app.core.config import (
    BaseAppSettings,
    DevelopmentSettings,
    EnvironmentType,
    ProductionSettings,
    TestingSettings,
    get_settings,
    settings,
)


def test_environment_type_enum():
    """Test the EnvironmentType enum."""
    assert EnvironmentType.DEVELOPMENT == "development"
    assert EnvironmentType.TESTING == "testing"
    assert EnvironmentType.PRODUCTION == "production"


def test_base_app_settings():
    """Test the BaseAppSettings class."""
    settings = BaseAppSettings()
    assert settings.PROJECT_NAME == "MAGPIE"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.ENVIRONMENT == EnvironmentType.DEVELOPMENT


def test_development_settings():
    """Test the DevelopmentSettings class."""
    # Create with explicit values to override any .env file settings
    settings = DevelopmentSettings(
        DEBUG=True,
        LOG_LEVEL="debug",
        ENVIRONMENT=EnvironmentType.DEVELOPMENT
    )
    assert settings.DEBUG is True
    assert settings.LOG_LEVEL == "debug"
    assert settings.ENVIRONMENT == EnvironmentType.DEVELOPMENT


def test_testing_settings():
    """Test the TestingSettings class."""
    # Create with explicit values to override any .env file settings
    settings = TestingSettings(
        DEBUG=True,
        LOG_LEVEL="debug",
        TESTING=True,
        ENVIRONMENT=EnvironmentType.TESTING,
        DATABASE_URL="sqlite:///./test.db"
    )
    assert settings.DEBUG is True
    assert settings.LOG_LEVEL == "debug"
    assert settings.TESTING is True
    assert settings.ENVIRONMENT == EnvironmentType.TESTING
    assert "sqlite" in settings.DATABASE_URL


def test_production_settings():
    """Test the ProductionSettings class."""
    # Create with explicit values to override any .env file settings
    settings = ProductionSettings(
        DEBUG=False,
        LOG_LEVEL="info",
        ENVIRONMENT=EnvironmentType.PRODUCTION
    )
    assert settings.DEBUG is False
    assert settings.LOG_LEVEL == "info"
    assert settings.ENVIRONMENT == EnvironmentType.PRODUCTION


@mock.patch.dict(os.environ, {"ENVIRONMENT": "development"})
def test_get_settings_development():
    """Test get_settings with development environment."""
    # Clear the lru_cache to ensure we get a fresh instance
    get_settings.cache_clear()
    settings = get_settings()
    assert isinstance(settings, DevelopmentSettings)
    assert settings.ENVIRONMENT == EnvironmentType.DEVELOPMENT


@mock.patch.dict(os.environ, {"ENVIRONMENT": "testing"})
def test_get_settings_testing():
    """Test get_settings with testing environment."""
    # Clear the lru_cache to ensure we get a fresh instance
    get_settings.cache_clear()
    settings = get_settings()
    assert isinstance(settings, TestingSettings)
    assert settings.ENVIRONMENT == EnvironmentType.TESTING
    assert hasattr(settings, "TESTING")
    assert settings.TESTING is True


@mock.patch.dict(os.environ, {"ENVIRONMENT": "production"})
def test_get_settings_production():
    """Test get_settings with production environment."""
    # Clear the lru_cache to ensure we get a fresh instance
    get_settings.cache_clear()
    settings = get_settings()
    assert isinstance(settings, ProductionSettings)
    assert settings.ENVIRONMENT == EnvironmentType.PRODUCTION
    assert settings.DEBUG is False


@mock.patch.dict(os.environ, {"ENVIRONMENT": "unknown"})
def test_get_settings_unknown():
    """Test get_settings with unknown environment."""
    # Clear the lru_cache to ensure we get a fresh instance
    get_settings.cache_clear()
    settings = get_settings()
    assert isinstance(settings, DevelopmentSettings)
    assert settings.ENVIRONMENT == EnvironmentType.DEVELOPMENT


def test_cors_origins_validator():
    """Test the CORS origins validator."""
    # Test with string input
    settings = BaseAppSettings(BACKEND_CORS_ORIGINS="http://localhost:3000,http://localhost:8000")
    assert len(settings.BACKEND_CORS_ORIGINS) == 2
    # AnyHttpUrl adds trailing slashes, so we need to check for them
    assert any("http://localhost:3000" in str(origin) for origin in settings.BACKEND_CORS_ORIGINS)
    assert any("http://localhost:8000" in str(origin) for origin in settings.BACKEND_CORS_ORIGINS)

    # Test with list input
    settings = BaseAppSettings(BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"])
    assert len(settings.BACKEND_CORS_ORIGINS) == 2
    assert any("http://localhost:3000" in str(origin) for origin in settings.BACKEND_CORS_ORIGINS)
    assert any("http://localhost:8000" in str(origin) for origin in settings.BACKEND_CORS_ORIGINS)

    # Test with JSON string input
    settings = BaseAppSettings(BACKEND_CORS_ORIGINS='["http://localhost:3000", "http://localhost:8000"]')
    assert len(settings.BACKEND_CORS_ORIGINS) == 2
    assert any("http://localhost:3000" in str(origin) for origin in settings.BACKEND_CORS_ORIGINS)
    assert any("http://localhost:8000" in str(origin) for origin in settings.BACKEND_CORS_ORIGINS)

    # Test with invalid input type
    with pytest.raises(ValueError):
        BaseAppSettings.assemble_cors_origins(123)

    # Test with malformed JSON string that causes JSONDecodeError
    result = BaseAppSettings.assemble_cors_origins('[not valid json')
    # Should return the original string
    assert result == '[not valid json'


def test_environment_variable_loading():
    """Test loading settings from environment variables."""
    env_vars = {
        "PROJECT_NAME": "TestProject",
        "API_V1_STR": "/api/v2",
        "DEBUG": "true",
        "LOG_LEVEL": "debug",
        "BACKEND_CORS_ORIGINS": '["http://example.com", "http://test.com"]',  # Must be valid JSON for complex types
        "AZURE_OPENAI_API_KEY": "test-key",
        "AZURE_OPENAI_ENDPOINT": "https://test-endpoint.openai.azure.com",
        "DATABASE_URL": "postgresql://user:password@localhost:5432/testdb",
        "REDIS_HOST": "redis-test",
        "REDIS_PORT": "6380",
        "REDIS_PASSWORD": "test-password"
    }

    with mock.patch.dict(os.environ, env_vars):
        # Clear the lru_cache to ensure we get a fresh instance
        get_settings.cache_clear()
        test_settings = DevelopmentSettings()

        # Verify environment variables are loaded correctly
        assert test_settings.PROJECT_NAME == "TestProject"
        assert test_settings.API_V1_STR == "/api/v2"
        assert test_settings.DEBUG is True
        assert test_settings.LOG_LEVEL == "debug"
        assert len(test_settings.BACKEND_CORS_ORIGINS) == 2
        assert test_settings.AZURE_OPENAI_API_KEY == "test-key"
        assert test_settings.AZURE_OPENAI_ENDPOINT == "https://test-endpoint.openai.azure.com"
        assert test_settings.DATABASE_URL == "postgresql://user:password@localhost:5432/testdb"
        assert test_settings.REDIS_HOST == "redis-test"
        assert test_settings.REDIS_PORT == 6380
        assert test_settings.REDIS_PASSWORD == "test-password"


def test_environment_variable_types():
    """Test that environment variables are converted to the correct types."""
    env_vars = {
        "DEBUG": "true",  # Should be converted to bool
        "REDIS_PORT": "6380",  # Should be converted to int
        "BACKEND_CORS_ORIGINS": '["http://example.com", "http://test.com"]'  # Should be converted to list
    }

    with mock.patch.dict(os.environ, env_vars):
        test_settings = BaseAppSettings()

        # Verify types are correct
        assert isinstance(test_settings.DEBUG, bool)
        assert test_settings.DEBUG is True

        assert isinstance(test_settings.REDIS_PORT, int)
        assert test_settings.REDIS_PORT == 6380

        assert isinstance(test_settings.BACKEND_CORS_ORIGINS, list)
        assert len(test_settings.BACKEND_CORS_ORIGINS) == 2


def test_missing_optional_environment_variables():
    """Test behavior with missing optional environment variables."""
    # Create a clean environment without any of our variables
    # We'll explicitly set DATABASE_URL to empty to override any .env file settings
    with mock.patch.dict(os.environ, {"DATABASE_URL": ""}, clear=True):
        test_settings = BaseAppSettings(
            DATABASE_URL="",  # Explicitly set to empty
            REDIS_PASSWORD="",
            AZURE_OPENAI_API_KEY="",
            AZURE_OPENAI_ENDPOINT=""
        )

        # Optional variables should have default values
        assert test_settings.DATABASE_URL == ""
        assert test_settings.REDIS_PASSWORD == ""
        assert test_settings.AZURE_OPENAI_API_KEY == ""
        assert test_settings.AZURE_OPENAI_ENDPOINT == ""


def test_environment_file_loading():
    """Test loading settings from environment files."""
    # Since we can't easily mock the file loading mechanism in pydantic_settings,
    # we'll test that the settings classes are configured with the correct env_file

    # Check that each settings class has the correct env_file in its model_config
    assert BaseAppSettings.model_config.get("env_file") == ".env"
    assert DevelopmentSettings.model_config.get("env_file") == ".env"
    assert TestingSettings.model_config.get("env_file") == ".env.test"
    assert ProductionSettings.model_config.get("env_file") == ".env.prod"

    # Test with environment variables to simulate file loading
    env_vars = {
        "PROJECT_NAME": "FileLoadedProject",
        "DEBUG": "true",
    }

    with mock.patch.dict(os.environ, env_vars):
        test_settings = TestingSettings()
        assert test_settings.PROJECT_NAME == "FileLoadedProject"
        assert test_settings.DEBUG is True


def test_settings_validation():
    """Test validation of settings values."""
    # Test validation of ENVIRONMENT enum
    with pytest.raises(ValidationError):
        BaseAppSettings(ENVIRONMENT="invalid")

    # Test validation of BACKEND_CORS_ORIGINS with invalid URL
    with pytest.raises(ValidationError):
        BaseAppSettings(BACKEND_CORS_ORIGINS=["not-a-url"])

    # Test validation of REDIS_PORT with invalid value
    with pytest.raises(ValidationError):
        BaseAppSettings(REDIS_PORT="not-an-int")


def test_settings_model_behavior():
    """Test the behavior of the settings model."""
    test_settings = BaseAppSettings()

    # Pydantic v2 models are mutable by default, so we can't test immutability
    # Instead, let's verify that the model behaves as expected

    # Verify that we can access settings attributes
    assert hasattr(test_settings, "PROJECT_NAME")
    assert test_settings.PROJECT_NAME == "MAGPIE"

    # Verify that the model has the expected methods
    assert hasattr(test_settings, "model_dump")
    assert callable(test_settings.model_dump)

    # Verify that model_dump returns a dictionary with the expected keys
    settings_dict = test_settings.model_dump()
    assert "PROJECT_NAME" in settings_dict
    assert "ENVIRONMENT" in settings_dict
    assert "DEBUG" in settings_dict


def test_settings_caching():
    """Test that the settings function uses caching."""
    # Get the initial settings instance
    initial_settings = get_settings()

    # Get the settings again without clearing the cache
    cached_settings = get_settings()

    # They should be the same object (due to lru_cache)
    assert initial_settings is cached_settings

    # After clearing the cache, we should get a new instance
    get_settings.cache_clear()
    new_settings = get_settings()

    # The settings should have the same values but be different instances
    assert new_settings is not initial_settings
    assert new_settings.PROJECT_NAME == initial_settings.PROJECT_NAME

    # The module-level settings variable should be the original instance
    assert settings is not new_settings


def test_environment_detection_precedence():
    """Test the precedence of environment detection."""
    # Test that explicit environment in constructor overrides env var
    with mock.patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        get_settings.cache_clear()
        test_settings = DevelopmentSettings(ENVIRONMENT=EnvironmentType.DEVELOPMENT)
        assert test_settings.ENVIRONMENT == EnvironmentType.DEVELOPMENT

        # But the global settings should still use the env var
        global_settings = get_settings()
        assert global_settings.ENVIRONMENT == EnvironmentType.PRODUCTION
