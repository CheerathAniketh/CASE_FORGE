import json
from typing import Optional
from upstash_redis.asyncio import Redis

from config import settings
from app.logger import get_logger

logger = get_logger(__name__)

_redis: Optional[Redis] = None


def get_redis() -> Optional[Redis]:
    """Lazily create the Upstash client. Returns None if not configured,
    so caching fails soft instead of crashing the app if env vars are missing."""
    global _redis
    if _redis is None and settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN:
        _redis = Redis(
            url=settings.UPSTASH_REDIS_REST_URL,
            token=settings.UPSTASH_REDIS_REST_TOKEN,
        )
    return _redis


async def cache_get(key: str) -> Optional[dict]:
    redis = get_redis()
    if redis is None:
        return None
    try:
        raw = await redis.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.warning(f"Cache get failed for {key}: {e}")
        return None


async def cache_set(key: str, value: dict, ttl_seconds: int = 60):
    redis = get_redis()
    if redis is None:
        return
    try:
        await redis.set(key, json.dumps(value), ex=ttl_seconds)
    except Exception as e:
        logger.warning(f"Cache set failed for {key}: {e}")


async def cache_delete(key: str):
    redis = get_redis()
    if redis is None:
        return
    try:
        await redis.delete(key)
    except Exception as e:
        logger.warning(f"Cache delete failed for {key}: {e}")