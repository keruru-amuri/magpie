"""Health check endpoints for MAGPIE platform."""

import time
from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()

# Store the application start time for uptime calculation
START_TIME = time.time()


@router.get("/health", summary="Health Check", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Health status information including environment, debug mode, and version.
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "version": settings.VERSION,
    }


@router.get("/health/health", summary="Standard Health Check", tags=["health"])
async def standard_health_check():
    """
    Standard health check endpoint.

    Returns:
        dict: Health status information including service statuses.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Placeholder for actual service checks
    return {
        "status": "ok",
        "version": settings.VERSION,
        "timestamp": timestamp,
        "environment": settings.ENVIRONMENT,
        "services": {
            "database": {
                "status": "ok",
                "latency_ms": 5,  # Placeholder value
            },
            "redis": {
                "status": "ok",
                "latency_ms": 2,  # Placeholder value
            },
            "azure_openai": {
                "status": "ok",
                "latency_ms": 150,  # Placeholder value
            },
        },
    }


@router.get("/health/ready", summary="Readiness Check", tags=["health"])
async def readiness_check():
    """
    Readiness check endpoint.

    Checks if the application is ready to handle requests.

    Returns:
        dict: Readiness status information.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Placeholder for actual readiness checks
    checks = [
        {
            "name": "database_connection",
            "status": "passed",
        },
        {
            "name": "redis_connection",
            "status": "passed",
        },
        {
            "name": "azure_openai_connection",
            "status": "passed",
        },
        {
            "name": "required_services",
            "status": "passed",
        },
    ]

    # If any check fails, the overall status is not_ready
    status = "ready"
    for check in checks:
        if check["status"] == "failed":
            status = "not_ready"
            break

    return {
        "status": status,
        "timestamp": timestamp,
        "checks": checks,
    }


@router.get("/health/live", summary="Liveness Check", tags=["health"])
async def liveness_check():
    """
    Liveness check endpoint.

    Checks if the application is alive and running.

    Returns:
        dict: Liveness status information.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    uptime_seconds = time.time() - START_TIME

    return {
        "status": "alive",
        "uptime_seconds": uptime_seconds,
        "timestamp": timestamp,
    }


@router.get("/health/detailed", summary="Detailed Health Check", tags=["health"])
async def detailed_health_check():
    """
    Detailed health check endpoint.

    Provides more detailed information about the system health including:
    - API status
    - Database connection status (placeholder)
    - Redis connection status (placeholder)
    - Azure OpenAI connection status (placeholder)

    Returns:
        dict: Detailed health status information.
    """
    # Placeholder for actual health checks
    return {
        "status": "healthy",
        "api": {
            "status": "operational",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        },
        "database": {
            "status": "operational",
            "connection": "placeholder",
        },
        "redis": {
            "status": "operational",
            "connection": "placeholder",
        },
        "azure_openai": {
            "status": "operational",
            "connection": "placeholder",
        },
    }
