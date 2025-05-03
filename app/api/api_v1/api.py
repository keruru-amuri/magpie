"""Main API router for API v1."""

from fastapi import APIRouter

from app.api.api_v1.endpoints import documentation, health, maintenance, troubleshooting

api_router = APIRouter()

# Include routers from endpoints
api_router.include_router(health.router, tags=["health"])
api_router.include_router(documentation.router, prefix="/documentation", tags=["documentation"])
api_router.include_router(troubleshooting.router, prefix="/troubleshooting", tags=["troubleshooting"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["maintenance"])
