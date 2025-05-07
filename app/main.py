"""Main application module for MAGPIE platform."""

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)

from app.api import api_router
from app.core.cache.connection import RedisCache
from app.core.config import settings, EnvironmentType
from app.core.logging import get_logger
from app.core.middleware import (
    LoggingMiddleware,
    RequestIdMiddleware,
    ErrorHandlingMiddleware,
    ProfilingMiddleware
)
from app.core.monitoring import (
    setup_tracing,
    TracingConfig,
    rotate_logs,
    AuditLogEvent,
    record_audit_log,
    get_performance_summary
)
from app.core.security.rate_limit import RateLimitMiddleware

# Configure logger
logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=None,  # Disable default docs to use custom docs
    redoc_url=None,  # Disable default redoc to use custom redoc
)

# Add request ID middleware (should be first in the chain)
app.add_middleware(RequestIdMiddleware)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Add error handling middleware
app.add_middleware(ErrorHandlingMiddleware)

# Add profiling middleware
if settings.ENVIRONMENT != EnvironmentType.TESTING:
    app.add_middleware(
        ProfilingMiddleware,
        enabled=settings.PERFORMANCE_PROFILING_ENABLED,
    )
    logger.info("Performance profiling middleware initialized")

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Set up rate limiting middleware
# Skip rate limiting for testing environment
if settings.ENVIRONMENT != EnvironmentType.TESTING:
    try:
        redis_cache = RedisCache(prefix="rate_limit")
        app.add_middleware(
            RateLimitMiddleware,
            redis_cache=redis_cache,
            rate_limit_per_minute=60,  # 60 requests per minute for regular endpoints
            auth_rate_limit_per_minute=5,  # 5 requests per minute for auth endpoints
            enabled=not settings.DEBUG,  # Disable in debug mode
        )
    except Exception as e:
        logger.warning(f"Failed to initialize rate limiting middleware: {e}")
        # Continue without rate limiting if Redis is not available

# Set up distributed tracing
if settings.ENVIRONMENT != EnvironmentType.TESTING:
    # Configure tracing
    tracing_config = TracingConfig(
        service_name=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        enabled=True,
        # Use different sampling rates based on environment
        sampling_ratio=0.1 if settings.ENVIRONMENT == EnvironmentType.PRODUCTION else 1.0,
        parent_based_sampling=True,
        console_export_enabled=settings.DEBUG,
        otlp_endpoint=os.getenv("OTLP_ENDPOINT"),
        # Configure batch processing for better performance
        batch_export_schedule_delay_millis=5000,  # 5 seconds in production
        batch_export_max_export_batch_size=512,
        batch_export_max_queue_size=2048,
        # Enable logging instrumentation to correlate logs with traces
        instrumentation_logging=True,
    )

    # Set up tracing
    setup_tracing(app, tracing_config)
    logger.info("Distributed tracing initialized with OpenTelemetry")

# Set up startup and shutdown events for log rotation
@app.on_event("startup")
async def startup_event():
    """Startup event for the application."""
    # Rotate logs on startup
    rotate_logs()
    logger.info("Log rotation initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event for the application."""
    # Perform final log rotation
    rotate_logs()
    logger.info("Final log rotation completed")

# Set up audit logging for key events
@app.middleware("http")
async def audit_logging_middleware(request: Request, call_next):
    """Middleware for audit logging of key events."""
    # Process the request
    response = await call_next(request)

    # Check if this is an authentication request
    if request.url.path.endswith("/login") and request.method == "POST":
        # Record login event with status based on response code
        record_audit_log(
            event_type=AuditLogEvent.USER_LOGIN,
            action="User login",
            # We can't easily extract the user ID from the response without modifying it,
            # so we'll leave it blank and rely on the IP and user agent for tracking
            user_id=None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            status="success" if response.status_code == 200 else "failure",
            details={
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
            },
        )

    # Check for user creation, update, or deletion events
    elif request.url.path.endswith("/users") and request.method == "POST":
        # User creation event
        record_audit_log(
            event_type=AuditLogEvent.USER_CREATED,
            action="User created",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            status="success" if response.status_code in (200, 201) else "failure",
        )

    # Return the original response
    return response

# Include API router
app.include_router(api_router)

# Custom documentation endpoints
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI documentation."""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{settings.PROJECT_NAME} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    """Swagger UI OAuth2 redirect."""
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """ReDoc documentation."""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{settings.PROJECT_NAME} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to MAGPIE - MAG Platform for Intelligent Execution",
        "version": settings.VERSION,
        "status": "operational",
        "documentation": "/docs",
        "api_version": settings.API_V1_STR,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
