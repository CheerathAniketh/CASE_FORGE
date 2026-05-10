import time
import ipaddress
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
        # In-memory and per-process by design (MVP-safe baseline).
        self.max_cache_size = 10000
        self.evict_batch_size = 1000

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path not in self.rate_limited_paths:
            return await call_next(request)

        client_ip = self._get_client_ip(request)

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

        # Periodic cleanup of stale entries first, then bounded eviction.
        if len(self.cache) > self.max_cache_size:
            stale_keys = [
                key for key, (window_start, _) in self.cache.items()
                if current_time - window_start > window
            ]
            for key in stale_keys:
                self.cache.pop(key, None)

            if len(self.cache) > self.max_cache_size:
                evicted = 0
                for key in list(self.cache.keys()):
                    self.cache.pop(key, None)
                    evicted += 1
                    if evicted >= self.evict_batch_size:
                        break

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

    def _get_client_ip(self, request: Request) -> str:
        direct_ip = request.client.host if request.client and request.client.host else "unknown"

        # Only trust X-Forwarded-For when immediate peer looks like a proxy/local hop.
        try:
            peer_ip = ipaddress.ip_address(direct_ip)
            trust_forwarded = peer_ip.is_loopback or peer_ip.is_private
        except ValueError:
            trust_forwarded = False

        if not trust_forwarded:
            return direct_ip

        forwarded = request.headers.get("X-Forwarded-For")
        if not forwarded:
            return direct_ip

        candidate = forwarded.split(",")[0].strip()
        try:
            ipaddress.ip_address(candidate)
            return candidate
        except ValueError:
            return direct_ip
