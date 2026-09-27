from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ready_success_when_dependencies_healthy(client: AsyncClient):
    """Ready check returns 200 when both Postgres and Redis respond."""
    with patch("app.main.check_db_health", new_callable=AsyncMock) as mock_db, \
         patch("app.main.check_redis_health", new_callable=AsyncMock) as mock_redis:
        mock_db.return_value = True
        mock_redis.return_value = True

        response = await client.get("/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_ready_fails_when_postgres_down(client: AsyncClient):
    """Ready check returns 503 with failed: ['postgres'] when DB is down."""
    with patch("app.main.check_db_health", new_callable=AsyncMock) as mock_db, \
         patch("app.main.check_redis_health", new_callable=AsyncMock) as mock_redis:
        mock_db.return_value = False
        mock_redis.return_value = True

        response = await client.get("/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unavailable"
        assert data["failed"] == ["postgres"]


@pytest.mark.asyncio
async def test_ready_fails_when_redis_down(client: AsyncClient):
    """Ready check returns 503 with failed: ['redis'] when Redis is down."""
    with patch("app.main.check_db_health", new_callable=AsyncMock) as mock_db, \
         patch("app.main.check_redis_health", new_callable=AsyncMock) as mock_redis:
        mock_db.return_value = True
        mock_redis.return_value = False

        response = await client.get("/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unavailable"
        assert data["failed"] == ["redis"]


@pytest.mark.asyncio
async def test_ready_fails_when_both_down(client: AsyncClient):
    """Ready check returns 503 listing both failed services."""
    with patch("app.main.check_db_health", new_callable=AsyncMock) as mock_db, \
         patch("app.main.check_redis_health", new_callable=AsyncMock) as mock_redis:
        mock_db.return_value = False
        mock_redis.return_value = False

        response = await client.get("/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unavailable"
        assert "postgres" in data["failed"]
        assert "redis" in data["failed"]
