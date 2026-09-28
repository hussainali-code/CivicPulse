import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.main import app
from app.models import Category, Complaint, Priority, Status
from app.providers.triage.base import TriageResult, get_triage_provider
from app.services.complaint_service import (
    ComplaintNotFoundException,
    ComplaintService,
    InvalidStateTransitionException,
    get_complaint_service,
)


@pytest.fixture
def mock_service():
    service = AsyncMock(spec=ComplaintService)
    return service


@pytest.fixture
def mock_provider():
    provider = AsyncMock()
    provider.name = "simulated"
    provider.triage.return_value = TriageResult(
        category=Category.WATER,
        priority=Priority.HIGH,
        summary="Water pipe burst causing road flooding",
        confidence=0.95,
    )
    return provider


@pytest.fixture
def sample_complaint():
    cid = uuid.uuid4()
    now = datetime.now(UTC)
    return Complaint(
        id=cid,
        text="Water pipe burst on 7th Avenue flooding the street",
        location="7th Avenue, Block C",
        reporter_contact="citizen@example.com",
        category=Category.WATER,
        priority=Priority.HIGH,
        status=Status.OPEN,
        ai_summary="Water pipe burst causing road flooding",
        triaged_by="simulated",
        triage_latency_ms=12,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_post_complaint_201_created(client: AsyncClient, mock_service, mock_provider, sample_complaint):
    """POST /api/complaints returns 201 and full complaint object."""
    mock_service.create.return_value = sample_complaint
    app.dependency_overrides[get_complaint_service] = lambda: mock_service
    app.dependency_overrides[get_triage_provider] = lambda: mock_provider

    try:
        response = await client.post(
            "/api/complaints",
            json={
                "text": "Water pipe burst on 7th Avenue flooding the street",
                "location": "7th Avenue, Block C",
                "reporter_contact": "citizen@example.com",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(sample_complaint.id)
        assert data["category"] == "water"
        assert data["priority"] == "high"
        assert data["status"] == "open"
        assert data["ai_summary"] == "Water pipe burst causing road flooding"
        assert data["triaged_by"] == "simulated"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_post_complaint_400_field_level_validation_error(client: AsyncClient):
    """POST /api/complaints with invalid fields returns 400 with field-level error body."""
    # Text under 10 chars, location under 3 chars
    response = await client.post(
        "/api/complaints",
        json={
            "text": "short",
            "location": "X",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    fields = [err["field"] for err in data["detail"]]
    assert "text" in fields or "location" in fields


@pytest.mark.asyncio
async def test_get_complaints_list_200_ok(client: AsyncClient, mock_service, sample_complaint):
    """GET /api/complaints returns 200 with paginated list and filters."""
    mock_service.list_all.return_value = ([sample_complaint], 1)
    app.dependency_overrides[get_complaint_service] = lambda: mock_service

    try:
        response = await client.get("/api/complaints?category=water&page=1&page_size=20")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(sample_complaint.id)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_complaint_by_id_200_ok(client: AsyncClient, mock_service, sample_complaint):
    """GET /api/complaints/{id} returns 200 for existing complaint."""
    mock_service.get_by_id.return_value = sample_complaint
    app.dependency_overrides[get_complaint_service] = lambda: mock_service

    try:
        response = await client.get(f"/api/complaints/{sample_complaint.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_complaint.id)
        assert data["location"] == sample_complaint.location
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_complaint_by_id_404_not_found(client: AsyncClient, mock_service):
    """GET /api/complaints/{id} returns 404 when complaint does not exist."""
    missing_id = uuid.uuid4()
    mock_service.get_by_id.side_effect = ComplaintNotFoundException(missing_id)
    app.dependency_overrides[get_complaint_service] = lambda: mock_service

    try:
        response = await client.get(f"/api/complaints/{missing_id}")
        assert response.status_code == 404
        data = response.json()
        assert f"complaint with id {missing_id} not found" in data["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_patch_complaint_status_valid_200_ok(client: AsyncClient, mock_service, sample_complaint):
    """PATCH /api/complaints/{id}/status returns 200 on valid state transition."""
    sample_complaint.status = Status.IN_PROGRESS
    mock_service.update_status.return_value = sample_complaint
    app.dependency_overrides[get_complaint_service] = lambda: mock_service

    try:
        response = await client.patch(
            f"/api/complaints/{sample_complaint.id}/status",
            json={"status": "in_progress"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_patch_complaint_status_invalid_409_conflict(client: AsyncClient, mock_service, sample_complaint):
    """PATCH /api/complaints/{id}/status returns 409 with exact cannot transition from {old} to {new} message."""
    mock_service.update_status.side_effect = InvalidStateTransitionException(Status.OPEN, Status.RESOLVED)
    app.dependency_overrides[get_complaint_service] = lambda: mock_service

    try:
        response = await client.patch(
            f"/api/complaints/{sample_complaint.id}/status",
            json={"status": "resolved"},
        )
        assert response.status_code == 409
        data = response.json()
        assert data["detail"] == "cannot transition from open to resolved"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_patch_complaint_status_not_found_404(client: AsyncClient, mock_service):
    """PATCH /api/complaints/{id}/status returns 404 when complaint does not exist."""
    missing_id = uuid.uuid4()
    mock_service.update_status.side_effect = ComplaintNotFoundException(missing_id)
    app.dependency_overrides[get_complaint_service] = lambda: mock_service

    try:
        response = await client.patch(
            f"/api/complaints/{missing_id}/status",
            json={"status": "in_progress"},
        )
        assert response.status_code == 404
        data = response.json()
        assert f"complaint with id {missing_id} not found" in data["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_meta_providers_200_ok(client: AsyncClient, mock_service):
    """GET /api/meta/providers returns active provider and last triage outcomes."""
    mock_service.get_last_triage_outcomes.return_value = [
        {"provider": "simulated", "latency_ms": 15, "fallback": False, "created_at": "2026-09-27T10:00:00Z"}
    ]
    app.dependency_overrides[get_complaint_service] = lambda: mock_service

    try:
        response = await client.get("/api/meta/providers")
        assert response.status_code == 200
        data = response.json()
        assert "active_provider" in data
        assert "outcomes" in data
        assert len(data["outcomes"]) == 1
        assert data["outcomes"][0]["provider"] == "simulated"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_stats_200_ok_with_cache_header(client: AsyncClient, mock_service):
    """GET /api/stats returns aggregates and sets X-Cache header."""
    from app.services.stats_service import get_stats_service

    mock_service.get_stats.return_value = (
        {
            "by_category": {"water": 5, "electricity": 3},
            "by_priority": {"high": 2, "normal": 6},
            "by_status": {"open": 7, "resolved": 1},
            "total": {"total": 8},
        },
        "MISS",
    )
    app.dependency_overrides[get_stats_service] = lambda: mock_service

    try:
        response = await client.get("/api/stats")
        assert response.status_code == 200
        assert response.headers.get("X-Cache") == "MISS"
        data = response.json()
        assert data["total"]["total"] == 8
        assert data["by_category"]["water"] == 5
    finally:
        app.dependency_overrides.clear()
