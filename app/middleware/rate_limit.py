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
    Async Rate Limiting Middleware with robust cache management.
    Handles proxies and implements localized cache cleanup.
    """

    def __init__(self, app):
        super().__init__(app)
        # Structure: { key: (timestamp_first_request, request_count) }
        self.cache: Dict[str, Tuple[float, int]] = {}
        self.rate_limited_paths = {"/api/v1/case-studies/generate"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path not in self.rate_limited_paths:
            return await call_next(request)

        # Handle proxies (X-Forwarded-For)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        cache_key = f"{client_ip}:{path}"
        
        limit = settings.RATE_LIMIT_REQUESTS
        window = settings.RATE_LIMIT_WINDOW

        # Stricter rate limits for the LLM generation endpoint (prevent cost spikes)
        limit = max(1, limit // 2)
        
        is_rate_limited = self._check_rate_limit(cache_key, limit, window)
        
        if is_rate_limited:
            logger.warning(
                "rate_limit_exceeded",
                extra={
                    "ip": client_ip,
                    "path": path,
                    "limit": limit
                }
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too Many Requests",
                    "detail": "Rate limit exceeded for case generation. Please wait a minute.",
                    "status_code": status.HTTP_429_TOO_MANY_REQUESTS
                },
                headers={"Retry-After": str(window)}
            )

        return await call_next(request)

    def _check_rate_limit(self, cache_key: str, limit: int, window: int) -> bool:
        current_time = time.time()
        
        # Periodic cleanup of stale entries without dumping the entire cache
        if len(self.cache) > 5000:
            # Sort by timestamp and remove oldest 1000 entries
            # This is a bit expensive but safer than clearing everything
            sorted_keys = sorted(self.cache.keys(), key=lambda k: self.cache[k][0])
            for k in sorted_keys[:1000]:
                del self.cache[k]

        if cache_key not in self.cache:
            self.cache[cache_key] = (current_time, 1)
            return False

        window_start, count = self.cache[cache_key]

        if current_time - window_start > window:
            # Window expired, reset
            self.cache[cache_key] = (current_time, 1)
            return False
            
        if count >= limit:
            return True

        # Increment count
        self.cache[cache_key] = (window_start, count + 1)
        return False
