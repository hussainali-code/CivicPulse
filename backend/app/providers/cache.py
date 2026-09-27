from typing import Optional
import redis.asyncio as aioredis
from app.config import get_settings

settings = get_settings()

redis_client: Optional[aioredis.Redis] = None


def get_redis_client() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(  # type: ignore[no-untyped-call]
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
        )
    return redis_client


async def close_redis_client() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None


async def check_redis_health() -> bool:
    """Check Redis reachability for the /ready probe with a short timeout."""
    try:
        client = get_redis_client()
        res = await client.ping()
        return bool(res)
    except Exception:
        return False
