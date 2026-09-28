import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

import redis.asyncio as aioredis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.providers.cache import get_redis_client
from app.repositories.complaint_repo import ComplaintRepository

logger = logging.getLogger("civicpulse")

STATS_KEY = "civicpulse:stats"
STATS_TTL = 30  # 30 seconds TTL per technical specification


class StatsService:
    def __init__(
        self,
        repo: ComplaintRepository | None = None,
        redis_client: aioredis.Redis | None = None,
        session: AsyncSession | None = None,
    ):
        self.repo = repo or ComplaintRepository()
        self.redis_client = redis_client
        self.session = session

    async def get_stats(
        self,
        redis_client: aioredis.Redis | None = None,
        session: AsyncSession | None = None
    ) -> tuple[dict[str, Any], str]:
        """
        Retrieves complaint statistics with Redis read-through caching.
        Returns: (stats_dict, 'HIT' | 'MISS')
        """
        r_client = redis_client if redis_client is not None else self.redis_client
        db_session = session if session is not None else self.session

        if db_session is None:
            raise ValueError("AsyncSession must be provided to fetch stats")

        # 1. Try Cache
        if r_client is not None:
            try:
                cached_data = await r_client.get(STATS_KEY)
                if cached_data is not None:
                    return json.loads(cached_data), "HIT"
            except Exception as exc:
                logger.warning(f"Redis get failed in StatsService, falling back to DB: {exc}")

        # 2. Cache Miss: Query Database
        stats = await self.repo.aggregate_stats(db_session)

        # 3. Populate Cache
        if r_client is not None:
            try:
                await r_client.setex(STATS_KEY, STATS_TTL, json.dumps(stats))
            except Exception as exc:
                logger.warning(f"Redis setex failed in StatsService: {exc}")

        return stats, "MISS"

    async def invalidate_stats(self, redis_client: aioredis.Redis | None = None) -> None:
        """Invalidate the cached statistics key in Redis."""
        r_client = redis_client if redis_client is not None else self.redis_client
        if r_client is not None:
            try:
                await r_client.delete(STATS_KEY)
            except Exception as exc:
                logger.warning(f"Redis cache invalidation failed: {exc}")


async def get_stats_service(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[StatsService, None]:
    client = get_redis_client()
    yield StatsService(redis_client=client, session=session)
