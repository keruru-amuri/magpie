"""
Rate limiting middleware for the MAGPIE platform.
"""
import logging
import time
from typing import Callable, Dict, Optional, Tuple

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from app.core.cache.connection import RedisCache

# Configure logging
logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting API requests.
    
    Uses Redis to track request counts and enforce rate limits.
    """
    
    def __init__(
        self,
        app: FastAPI,
        redis_cache: Optional[RedisCache] = None,
        rate_limit_per_minute: int = 60,
        auth_rate_limit_per_minute: int = 5,
        enabled: bool = True,
    ):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application
            redis_cache: Redis cache instance
            rate_limit_per_minute: Rate limit for regular endpoints
            auth_rate_limit_per_minute: Rate limit for authentication endpoints
            enabled: Whether rate limiting is enabled
        """
        super().__init__(app)
        self.redis_cache = redis_cache or RedisCache(prefix="rate_limit")
        self.rate_limit_per_minute = rate_limit_per_minute
        self.auth_rate_limit_per_minute = auth_rate_limit_per_minute
        self.enabled = enabled
        
        # Define paths that have special rate limits
        self.auth_paths = {
            "/api/v1/auth/login",
            "/api/v1/auth/login/access-token",
            "/api/v1/auth/register",
        }
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process the request and apply rate limiting.
        
        Args:
            request: HTTP request
            call_next: Next middleware or endpoint
            
        Returns:
            Response: HTTP response
        """
        if not self.enabled:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Get path
        path = request.url.path
        
        # Determine rate limit based on path
        is_auth_path = path in self.auth_paths
        rate_limit = self.auth_rate_limit_per_minute if is_auth_path else self.rate_limit_per_minute
        
        # Check rate limit
        allowed, current_count, ttl = await self._check_rate_limit(client_ip, path, rate_limit)
        
        # Add rate limit headers to response
        response = await call_next(request) if allowed else self._rate_limit_exceeded_response()
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, rate_limit - current_count))
        if ttl > 0:
            response.headers["X-RateLimit-Reset"] = str(ttl)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request.
        
        Args:
            request: HTTP request
            
        Returns:
            str: Client IP address
        """
        # Try to get IP from X-Forwarded-For header
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, use the first one
            return forwarded_for.split(",")[0].strip()
        
        # Fall back to client.host
        return request.client.host if request.client else "unknown"
    
    async def _check_rate_limit(
        self, client_ip: str, path: str, rate_limit: int
    ) -> Tuple[bool, int, int]:
        """
        Check if a request is within rate limits.
        
        Args:
            client_ip: Client IP address
            path: Request path
            rate_limit: Rate limit per minute
            
        Returns:
            Tuple[bool, int, int]: (allowed, current_count, ttl)
        """
        # Create a key for this IP and path
        # Use a sliding window of 60 seconds
        minute = int(time.time() / 60)
        key = f"rate_limit:{client_ip}:{path}:{minute}"
        
        try:
            # Increment the counter
            count = self.redis_cache.redis.incr(key)
            
            # Set expiration if this is a new key
            if count == 1:
                self.redis_cache.redis.expire(key, 60)
            
            # Get TTL
            ttl = self.redis_cache.redis.ttl(key)
            
            # Check if rate limit is exceeded
            if count > rate_limit:
                logger.warning(
                    f"Rate limit exceeded for {client_ip} on {path}: {count}/{rate_limit}"
                )
                return False, count, ttl
            
            return True, count, ttl
        except Exception as e:
            # If Redis fails, allow the request but log the error
            logger.error(f"Error checking rate limit: {str(e)}")
            return True, 0, 0
    
    def _rate_limit_exceeded_response(self) -> JSONResponse:
        """
        Create a response for rate limit exceeded.
        
        Returns:
            JSONResponse: Rate limit exceeded response
        """
        return JSONResponse(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Rate limit exceeded. Please try again later.",
            },
        )
