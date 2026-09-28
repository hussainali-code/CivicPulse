from unittest.mock import patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient):
    """Health check must return 200 OK with status: ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_never_touches_db_or_redis(client: AsyncClient):
    """Health check must remain 200 OK even if DB and Redis are completely unreachable."""
    with patch("app.db.check_db_health", side_effect=Exception("DB connection failure")), \
         patch("app.providers.cache.check_redis_health", side_effect=Exception("Redis connection failure")):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
