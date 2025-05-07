"""
Distributed tracing for the MAGPIE platform.

This module provides distributed tracing functionality using OpenTelemetry.
It allows for tracing requests across service boundaries and visualizing
the flow of requests through the system.
"""

import os
import socket
from functools import lru_cache
from typing import Dict, Optional, List, Any, Callable

from fastapi import FastAPI, Request, Response
from loguru import logger
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, DEPLOYMENT_ENVIRONMENT
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased, ParentBasedTraceIdRatio
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings


# Configure logger
logger = logger.bind(name=__name__)


class TracingConfig:
    """Configuration for distributed tracing."""

    def __init__(
        self,
        service_name: str = settings.PROJECT_NAME,
        environment: str = settings.ENVIRONMENT,
        version: str = settings.VERSION,
        enabled: bool = True,
        sampling_ratio: float = 0.5,  # Default to 50% sampling for production
        parent_based_sampling: bool = True,  # Use parent-based sampling by default
        console_export_enabled: bool = settings.DEBUG,
        otlp_endpoint: Optional[str] = os.getenv("OTLP_ENDPOINT"),
        otlp_headers: Optional[Dict[str, str]] = None,
        otlp_timeout: float = 10.0,  # Timeout in seconds
        batch_export_schedule_delay_millis: int = 5000,  # 5 seconds
        batch_export_max_export_batch_size: int = 512,
        batch_export_max_queue_size: int = 2048,
        instrumentation_logging: bool = True,  # Enable logging instrumentation
    ):
        """
        Initialize tracing configuration.

        Args:
            service_name: Name of the service
            environment: Environment (e.g., development, production)
            version: Service version
            enabled: Whether tracing is enabled
            sampling_ratio: Sampling ratio (0.0 to 1.0)
            parent_based_sampling: Whether to use parent-based sampling
            console_export_enabled: Whether to export spans to console
            otlp_endpoint: OpenTelemetry collector endpoint
            otlp_headers: Headers for OTLP exporter
            otlp_timeout: Timeout for OTLP exporter in seconds
            batch_export_schedule_delay_millis: Delay between two consecutive exports
            batch_export_max_export_batch_size: Maximum batch size for export
            batch_export_max_queue_size: Maximum queue size for export
            instrumentation_logging: Whether to instrument logging
        """
        self.service_name = service_name
        self.environment = environment
        self.version = version
        self.enabled = enabled
        self.sampling_ratio = sampling_ratio
        self.parent_based_sampling = parent_based_sampling
        self.console_export_enabled = console_export_enabled
        self.otlp_endpoint = otlp_endpoint
        self.otlp_headers = otlp_headers or {}
        self.otlp_timeout = otlp_timeout
        self.batch_export_schedule_delay_millis = batch_export_schedule_delay_millis
        self.batch_export_max_export_batch_size = batch_export_max_export_batch_size
        self.batch_export_max_queue_size = batch_export_max_queue_size
        self.instrumentation_logging = instrumentation_logging


@lru_cache()
def get_tracer_provider(config: TracingConfig) -> Optional[TracerProvider]:
    """
    Get a tracer provider with the given configuration.

    Args:
        config: Tracing configuration

    Returns:
        TracerProvider: Configured tracer provider or None if disabled
    """
    if not config.enabled:
        logger.info("Distributed tracing is disabled")
        return None

    # Create a resource with service information
    hostname = socket.gethostname()
    resource = Resource.create({
        SERVICE_NAME: config.service_name,
        DEPLOYMENT_ENVIRONMENT: config.environment,
        "service.version": config.version,
        "service.instance.id": hostname,
        "host.name": hostname,
    })

    # Create a sampler based on configuration
    if config.parent_based_sampling:
        # Use parent-based sampling (respects parent span's sampling decision)
        sampler = ParentBasedTraceIdRatio(config.sampling_ratio)
    else:
        # Use simple trace ID ratio-based sampling
        sampler = TraceIdRatioBased(config.sampling_ratio)

    # Create a tracer provider with the resource and sampler
    tracer_provider = TracerProvider(
        resource=resource,
        sampler=sampler,
    )

    # Add console exporter if enabled
    if config.console_export_enabled:
        console_exporter = ConsoleSpanExporter()
        console_processor = BatchSpanProcessor(
            console_exporter,
            # Use smaller batches for console to see results faster
            max_export_batch_size=256,
            schedule_delay_millis=1000,
        )
        tracer_provider.add_span_processor(console_processor)

    # Add OTLP exporter if configured
    if config.otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(
            endpoint=config.otlp_endpoint,
            headers=config.otlp_headers,
            timeout=config.otlp_timeout,
        )
        otlp_processor = BatchSpanProcessor(
            otlp_exporter,
            max_export_batch_size=config.batch_export_max_export_batch_size,
            schedule_delay_millis=config.batch_export_schedule_delay_millis,
            max_queue_size=config.batch_export_max_queue_size,
        )
        tracer_provider.add_span_processor(otlp_processor)

    # Set the tracer provider as the global provider
    trace.set_tracer_provider(tracer_provider)

    logger.info(
        f"Distributed tracing initialized for {config.service_name} "
        f"in {config.environment} environment with {config.sampling_ratio * 100:.1f}% sampling"
    )

    return tracer_provider


def get_tracer(name: str = __name__) -> trace.Tracer:
    """
    Get a tracer for the given name.

    Args:
        name: Name of the tracer (usually __name__)

    Returns:
        Tracer: OpenTelemetry tracer
    """
    return trace.get_tracer(name)


def create_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    kind: Optional[trace.SpanKind] = None,
) -> trace.Span:
    """
    Create a new span.

    Args:
        name: Name of the span
        attributes: Span attributes
        kind: Span kind

    Returns:
        Span: OpenTelemetry span
    """
    tracer = get_tracer()
    return tracer.start_span(
        name=name,
        attributes=attributes,
        kind=kind,
    )


def trace_function(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    kind: Optional[trace.SpanKind] = None,
):
    """
    Decorator to trace a function.

    Args:
        name: Name of the span (defaults to function name)
        attributes: Span attributes
        kind: Span kind

    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get span name from parameter or function name
            span_name = name or func.__name__

            # Get tracer
            tracer = get_tracer()

            # Start a span
            with tracer.start_as_current_span(
                name=span_name,
                attributes=attributes,
                kind=kind,
            ) as span:
                # Add function arguments as span attributes if not sensitive
                if args:
                    for i, arg in enumerate(args):
                        if isinstance(arg, (str, int, float, bool)):
                            span.set_attribute(f"arg_{i}", str(arg))

                # Add keyword arguments as span attributes if not sensitive
                for key, value in kwargs.items():
                    if isinstance(value, (str, int, float, bool)) and not _is_sensitive(key):
                        span.set_attribute(key, str(value))

                # Call the original function
                result = func(*args, **kwargs)

                return result

        return wrapper

    return decorator


def _is_sensitive(key: str) -> bool:
    """
    Check if a key might contain sensitive information.

    Args:
        key: Key to check

    Returns:
        bool: True if the key might contain sensitive information
    """
    sensitive_patterns = [
        "password", "token", "secret", "key", "auth", "credential", "jwt",
        "api_key", "apikey", "access_token", "refresh_token", "private_key",
    ]

    return any(pattern in key.lower() for pattern in sensitive_patterns)


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for distributed tracing.

    This middleware adds distributed tracing to HTTP requests and
    propagates trace context across service boundaries.
    """

    def __init__(self, app: ASGIApp):
        """
        Initialize the middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)
        self.propagator = TraceContextTextMapPropagator()
        self.logger = logger.bind(name=__name__)

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process the request and add tracing.

        Args:
            request: FastAPI request
            call_next: Next middleware or route handler

        Returns:
            Response: FastAPI response
        """
        # Extract trace context from request headers
        carrier = {k.lower(): v for k, v in request.headers.items()}
        context = self.propagator.extract(carrier=carrier)

        # Get tracer
        tracer = get_tracer()

        # Start a span for the request
        with tracer.start_as_current_span(
            name=f"{request.method} {request.url.path}",
            context=context,
            kind=trace.SpanKind.SERVER,
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.host": request.url.hostname or "",
                "http.scheme": request.url.scheme or "",
                "http.target": request.url.path,
                "http.client_ip": request.client.host if request.client else "",
                "http.user_agent": request.headers.get("user-agent", ""),
                "http.request_id": getattr(request.state, "request_id", ""),
            },
        ) as span:
            # Process the request
            response = await call_next(request)

            # Add response attributes to the span
            span.set_attribute("http.status_code", response.status_code)

            # Add trace context to response headers
            carrier = {}
            self.propagator.inject(carrier=carrier)
            for key, value in carrier.items():
                response.headers[key] = value

            return response


def setup_tracing(app: FastAPI, config: Optional[TracingConfig] = None) -> None:
    """
    Set up distributed tracing for a FastAPI application.

    Args:
        app: FastAPI application
        config: Tracing configuration
    """
    # Use default config if not provided
    if config is None:
        config = TracingConfig()

    # Skip if tracing is disabled
    if not config.enabled:
        logger.info("Distributed tracing is disabled")
        return

    # Initialize tracer provider
    tracer_provider = get_tracer_provider(config)

    # Skip if tracer provider initialization failed
    if tracer_provider is None:
        logger.warning("Failed to initialize tracer provider")
        return

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)

    # Instrument HTTPX for outgoing requests
    HTTPXClientInstrumentor().instrument(tracer_provider=tracer_provider)

    # Instrument Redis
    RedisInstrumentor().instrument(tracer_provider=tracer_provider)

    # Instrument logging if enabled
    if config.instrumentation_logging:
        LoggingInstrumentor().instrument(
            tracer_provider=tracer_provider,
            set_logging_format=True,
            log_level=20,  # INFO level
        )
        logger.info("Logging instrumentation enabled")

    # Add tracing middleware
    app.add_middleware(TracingMiddleware)

    logger.info(
        f"Distributed tracing set up successfully for {config.service_name} "
        f"with sampling ratio {config.sampling_ratio:.2f}"
    )


def extract_trace_context(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Extract trace context from headers.

    Args:
        headers: HTTP headers

    Returns:
        Dict[str, str]: Trace context headers
    """
    propagator = TraceContextTextMapPropagator()
    carrier = {}
    propagator.inject(carrier=carrier)

    # Filter out only the trace context headers from the original headers
    trace_headers = {}
    for key in carrier:
        if key.lower() in headers:
            trace_headers[key] = headers[key.lower()]

    return trace_headers


def inject_trace_context(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Inject trace context into headers.

    Args:
        headers: HTTP headers

    Returns:
        Dict[str, str]: Headers with trace context
    """
    propagator = TraceContextTextMapPropagator()
    carrier = headers.copy()
    propagator.inject(carrier=carrier)
    return carrier
