import logging
from typing import Any

import redis.asyncio as aioredis
from fastapi import Depends, Request

from app.providers.cache import get_redis_client

logger = logging.getLogger("civicpulse")

RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60


class RateLimitExceeded(Exception):
    """Exception raised when an IP exceeds allowed request quota."""

    def __init__(self, retry_after: int = 60, detail: str = "rate limit exceeded"):
        self.retry_after = retry_after
        self.detail = detail
        super().__init__(detail)


def get_client_ip(request: Request) -> str:
    """Extract client IP from X-Forwarded-For header or fallback to request.client.host."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # First IP in comma-separated list is client IP
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


async def check_rate_limit(redis_client: Any, ip: str) -> None:
    """
    Fixed-window rate limiter using Redis INCR and EXPIRE.
    Allows 10 requests per 60-second window per IP.
    Exceeding limit raises RateLimitExceeded with remaining TTL in seconds.
    """
    key = f"civicpulse:rl:{ip}"

    try:
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, RATE_LIMIT_WINDOW_SECONDS)

        if count > RATE_LIMIT_MAX_REQUESTS:
            ttl = await redis_client.ttl(key)
            retry_after = max(int(ttl), 1) if ttl is not None and ttl > 0 else RATE_LIMIT_WINDOW_SECONDS
            logger.warning(
                f"Rate limit exceeded for IP {ip} ({count}/{RATE_LIMIT_MAX_REQUESTS}). Retry-After: {retry_after}s"
            )
            raise RateLimitExceeded(retry_after=retry_after)
    except RateLimitExceeded:
        raise
    except Exception as exc:
        # If Redis is temporarily down, do not block traffic (fail-open for resilience)
        logger.error(f"Redis rate limiter check encountered error, failing open: {exc}")


async def rate_limit_dependency(
    request: Request,
    redis: aioredis.Redis = Depends(get_redis_client),
) -> None:
    """FastAPI dependency to rate-limit incoming HTTP endpoints by client IP."""
    ip = get_client_ip(request)
    await check_rate_limit(redis, ip)
