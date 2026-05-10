import time
from typing import Dict, Tuple
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Async Rate Limiting Middleware for FastAPI.
    
    Implements an in-memory sliding window rate limiter for Phase 1.
    Designed to be easily swapped with Redis in Phase 2 for horizontal scaling.
    """

    def __init__(self, app):
        super().__init__(app)
        # Structure: { ip_address:path: (timestamp_first_request, request_count) }
        self.cache: Dict[str, Tuple[float, int]] = {}
        self.rate_limited_paths = {"/api/v1/case-studies/generate"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path not in self.rate_limited_paths:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        cache_key = f"{client_ip}:{path}"
        
        limit = settings.RATE_LIMIT_REQUESTS
        window = settings.RATE_LIMIT_WINDOW

        # Stricter rate limits for the LLM generation endpoint
        limit = max(1, limit // 5)
        
        is_rate_limited = self._check_rate_limit(cache_key, limit, window)
        
        if is_rate_limited:
            logger.warning(
                "rate_limit_exceeded",
                extra={
                    "ip": client_ip,
                    "path": path,
                    "limit": limit,
                    "window": window
                }
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too Many Requests",
                    "detail": "Rate limit exceeded. Please try again later.",
                    "status_code": status.HTTP_429_TOO_MANY_REQUESTS
                },
                headers={"Retry-After": str(window)}
            )

        return await call_next(request)

    def _check_rate_limit(self, cache_key: str, limit: int, window: int) -> bool:
        current_time = time.time()
        
        # Periodic cleanup of stale entries (Phase 1 simplistic memory management)
        if len(self.cache) > 10000:
            self.cache = {
                key: data for key, data in self.cache.items() 
                if (current_time - data[0]) < window
            }

        if cache_key not in self.cache:
            self.cache[cache_key] = (current_time, 1)
            return False

        window_start, count = self.cache[cache_key]

        if current_time - window_start > window:
            self.cache[cache_key] = (current_time, 1)
            return False
            
        if count >= limit:
            return True

        self.cache[cache_key] = (window_start, count + 1)
        return False
