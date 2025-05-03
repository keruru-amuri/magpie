"""Health check endpoints for MAGPIE platform."""

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


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
