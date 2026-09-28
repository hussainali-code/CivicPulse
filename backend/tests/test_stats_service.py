import json
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.main import app
from app.services.stats_service import (
    STATS_KEY,
    STATS_TTL,
    StatsService,
    get_stats_service,
)


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.aggregate_stats.return_value = {
        "by_category": {"water": 5, "roads": 2},
        "by_priority": {"high": 3, "normal": 4},
        "by_status": {"open": 6, "resolved": 1},
        "total": {"total": 7},
    }
    return repo


@pytest.mark.asyncio
async def test_stats_cache_miss_populates_redis(mock_repo):
    session = AsyncMock()
    redis_client = AsyncMock()
    redis_client.get.return_value = None  # Cache miss

    service = StatsService(repo=mock_repo, redis_client=redis_client, session=session)
    data, cache_status = await service.get_stats()

    assert cache_status == "MISS"
    assert data["by_category"]["water"] == 5
    mock_repo.aggregate_stats.assert_awaited_once_with(session)
    redis_client.setex.assert_awaited_once_with(
        STATS_KEY, STATS_TTL, json.dumps(data)
    )


@pytest.mark.asyncio
async def test_stats_cache_hit_returns_cached_data_without_db(mock_repo):
    session = AsyncMock()
    redis_client = AsyncMock()
    cached_payload = {
        "by_category": {"water": 10},
        "by_priority": {"high": 10},
        "by_status": {"open": 10},
        "total": {"total": 10},
    }
    redis_client.get.return_value = json.dumps(cached_payload)  # Cache hit

    service = StatsService(repo=mock_repo, redis_client=redis_client, session=session)
    data, cache_status = await service.get_stats()

    assert cache_status == "HIT"
    assert data["total"]["total"] == 10
    mock_repo.aggregate_stats.assert_not_awaited()


@pytest.mark.asyncio
async def test_stats_cache_invalidation():
    redis_client = AsyncMock()
    service = StatsService(redis_client=redis_client)
    await service.invalidate_stats()
    redis_client.delete.assert_awaited_once_with(STATS_KEY)


@pytest.mark.asyncio
async def test_get_stats_route_header_hit_and_miss(client: AsyncClient):
    mock_service = AsyncMock()
    sample_stats = {
        "by_category": {"water": 5},
        "by_priority": {"high": 5},
        "by_status": {"open": 5},
        "total": {"total": 5},
    }

    # 1. First call: MISS
    mock_service.get_stats.return_value = (sample_stats, "MISS")
    app.dependency_overrides[get_stats_service] = lambda: mock_service

    res1 = await client.get("/api/stats")
    assert res1.status_code == 200
    assert res1.headers.get("X-Cache") == "MISS"

    # 2. Second call: HIT
    mock_service.get_stats.return_value = (sample_stats, "HIT")
    res2 = await client.get("/api/stats")
    assert res2.status_code == 200
    assert res2.headers.get("X-Cache") == "HIT"

    app.dependency_overrides.clear()
