import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_prometheus_format(client: AsyncClient):
    """Metrics endpoint must return 200 with Prometheus text output."""
    # First make a request so metrics get populated
    await client.get("/health")

    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "requests_total" in response.text
    assert "request_latency_seconds" in response.text
