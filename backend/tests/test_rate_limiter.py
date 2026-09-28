import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.main import app
from app.models import Category, Complaint, Priority, Status
from app.providers.cache import get_redis_client
from app.providers.rate_limiter import (
    RateLimitExceeded,
    check_rate_limit,
)
from app.providers.triage.base import TriageResult, get_triage_provider
from app.services.complaint_service import ComplaintService, get_complaint_service


class MockRedisRateLimiter:
    """Mock Redis client simulating INCR, EXPIRE, and TTL semantics."""

    def __init__(self, remaining_ttl: int = 42):
        self.counters = {}
        self.ttls = {}
        self.remaining_ttl = remaining_ttl

    async def incr(self, key: str) -> int:
        count = self.counters.get(key, 0) + 1
        self.counters[key] = count
        return count

    async def expire(self, key: str, seconds: int) -> bool:
        return True

    async def ttl(self, key: str) -> int:
        return self.remaining_ttl

    async def delete(self, key: str) -> int:
        self.counters.pop(key, None)
        return 1


@pytest.mark.asyncio
async def test_check_rate_limit_allows_ten_requests():
    """check_rate_limit allows up to 10 requests within window without raising."""
    mock_redis = MockRedisRateLimiter(remaining_ttl=60)
    test_ip = "192.168.1.100"

    for _ in range(10):
        await check_rate_limit(mock_redis, test_ip)

    assert mock_redis.counters[f"civicpulse:rl:{test_ip}"] == 10


@pytest.mark.asyncio
async def test_check_rate_limit_eleventh_request_raises_rate_limit_exceeded():
    """check_rate_limit raises RateLimitExceeded on the 11th request with TTL."""
    mock_redis = MockRedisRateLimiter(remaining_ttl=42)
    test_ip = "192.168.1.101"

    for _ in range(10):
        await check_rate_limit(mock_redis, test_ip)

    with pytest.raises(RateLimitExceeded) as exc_info:
        await check_rate_limit(mock_redis, test_ip)

    assert exc_info.value.retry_after == 42
    assert exc_info.value.detail == "rate limit exceeded"


@pytest.mark.asyncio
async def test_post_complaints_rate_limiting_integration(client: AsyncClient):
    """POST /api/complaints permits 10 requests and rejects 11th with 429 and Retry-After."""
    mock_redis = MockRedisRateLimiter(remaining_ttl=30)
    mock_service = AsyncMock(spec=ComplaintService)
    mock_provider = AsyncMock()
    mock_provider.name = "simulated"
    mock_provider.triage.return_value = TriageResult(
        category=Category.WATER,
        priority=Priority.NORMAL,
        summary="Water pipe issue",
        confidence=0.90,
    )

    sample_complaint = Complaint(
        id=uuid.uuid4(),
        text="Water main leak causing localized puddle",
        location="Sector G-9",
        reporter_contact=None,
        category=Category.WATER,
        priority=Priority.NORMAL,
        status=Status.OPEN,
        ai_summary="Water main leak",
        triaged_by="simulated",
        triage_latency_ms=10,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    mock_service.create.return_value = sample_complaint

    app.dependency_overrides[get_redis_client] = lambda: mock_redis
    app.dependency_overrides[get_complaint_service] = lambda: mock_service
    app.dependency_overrides[get_triage_provider] = lambda: mock_provider

    try:
        payload = {
            "text": "Water main leak causing localized puddle",
            "location": "Sector G-9",
        }
        headers = {"X-Forwarded-For": "203.0.113.195"}

        # 1. First 10 requests should succeed with 201 Created
        for i in range(10):
            response = await client.post("/api/complaints", json=payload, headers=headers)
            assert response.status_code == 201, f"Request {i+1} failed with status {response.status_code}"

        # 2. 11th request from SAME IP must fail with 429 Too Many Requests
        response_11 = await client.post("/api/complaints", json=payload, headers=headers)
        assert response_11.status_code == 429
        assert response_11.json() == {"detail": "rate limit exceeded"}
        assert "Retry-After" in response_11.headers
        assert response_11.headers["Retry-After"] == "30"

        # 3. A different IP is NOT blocked and receives 201 Created
        diff_headers = {"X-Forwarded-For": "203.0.113.196"}
        response_diff = await client.post("/api/complaints", json=payload, headers=diff_headers)
        assert response_diff.status_code == 201

    finally:
        app.dependency_overrides.clear()
