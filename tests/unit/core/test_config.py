"""Tests for the configuration module."""

import os
from unittest import mock

import pytest

from app.core.config import (
    BaseAppSettings,
    DevelopmentSettings,
    EnvironmentType,
    ProductionSettings,
    TestingSettings,
    get_settings,
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
