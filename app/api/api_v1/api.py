"""Main API router for API v1."""

from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    analytics,
    auth,
    chat,
    context,
    database,
    documentation,
    errors,
    health,
    maintenance,
    metrics,
    orchestrator,
    tools_and_parts,
    troubleshooting,
    users,
    safety_precautions,
    websocket,
)

from app.api.endpoints import monitoring

api_router = APIRouter()

# Include routers from endpoints
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(context.router, prefix="/context", tags=["context"])
api_router.include_router(documentation.router, prefix="/documentation", tags=["documentation"])
api_router.include_router(troubleshooting.router, prefix="/troubleshooting", tags=["troubleshooting"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["maintenance"])
api_router.include_router(orchestrator.router, prefix="/orchestrator", tags=["orchestrator"])
api_router.include_router(tools_and_parts.router, prefix="/resources", tags=["resources"])
api_router.include_router(safety_precautions.router, prefix="/safety", tags=["safety"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(errors.router, prefix="/errors", tags=["errors"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(database.router, prefix="/database", tags=["database"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(websocket.router, tags=["websocket"])
