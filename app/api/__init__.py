"""API package for MAGPIE platform."""

from fastapi import APIRouter

from app.api.api_v1.api import api_router as api_v1_router
from app.core.config import settings

# Create main API router
api_router = APIRouter()

# Include API version routers
api_router.include_router(api_v1_router, prefix=settings.API_V1_STR)
