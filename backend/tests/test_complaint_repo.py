import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import Category, Complaint, Priority, Status
from app.repositories.complaint_repo import ComplaintRepository


@pytest.fixture
def repo():
    return ComplaintRepository()


@pytest.mark.asyncio
async def test_repo_create(repo):
    session = AsyncMock()
    session.add = MagicMock()
    complaint = await repo.create(
        session,
        text="Streetlight broken outside street 4",
        location="Street 4, Sector G-10",
        reporter_contact="test@example.com",
        category=Category.STREETLIGHTS,
        priority=Priority.LOW,
        ai_summary="Broken streetlight reported.",
        triaged_by="simulated",
        triage_latency_ms=15,
    )
    assert complaint.text == "Streetlight broken outside street 4"
    assert complaint.category == Category.STREETLIGHTS
    assert complaint.status == Status.OPEN
    session.add.assert_called_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_repo_get_by_id(repo):
    session = AsyncMock()
    cid = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Complaint(
        id=cid,
        text="Broken pipe",
        location="Test Loc",
        category=Category.WATER,
        priority=Priority.HIGH,
        status=Status.OPEN,
        triaged_by="simulated",
        triage_latency_ms=10,
    )
    session.execute.return_value = mock_result

    res = await repo.get_by_id(session, cid)
    assert res is not None
    assert res.id == cid


@pytest.mark.asyncio
async def test_repo_list_filtered(repo):
    session = AsyncMock()
    cid = uuid.uuid4()
    
    # Mock count query result
    mock_count_res = MagicMock()
    mock_count_res.scalar_one.return_value = 1
    
    # Mock list query result
    mock_list_res = MagicMock()
    mock_complaint = Complaint(
        id=cid,
        text="Broken pipe",
        location="Test Loc",
        category=Category.WATER,
        priority=Priority.HIGH,
        status=Status.OPEN,
        triaged_by="simulated",
        triage_latency_ms=10,
    )
    mock_list_res.scalars.return_value.all.return_value = [mock_complaint]

    session.execute.side_effect = [mock_count_res, mock_list_res]

    items, total = await repo.list_filtered(
        session,
        category=Category.WATER,
        priority=Priority.HIGH,
        status=Status.OPEN,
        page=1,
        page_size=20
    )
    assert total == 1
    assert len(items) == 1
    assert items[0].id == cid


@pytest.mark.asyncio
async def test_repo_update_status(repo):
    session = AsyncMock()
    session.add = MagicMock()
    complaint = Complaint(
        id=uuid.uuid4(),
        text="Broken pipe",
        location="Test Loc",
        category=Category.WATER,
        priority=Priority.HIGH,
        status=Status.OPEN,
        triaged_by="simulated",
        triage_latency_ms=10,
    )
    updated = await repo.update_status(session, complaint, Status.IN_PROGRESS)
    assert updated.status == Status.IN_PROGRESS
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_repo_aggregate_stats(repo):
    session = AsyncMock()
    
    # Mock 3 groupby queries
    mock_cat = MagicMock()
    mock_cat.all.return_value = [(Category.WATER, 5), (Category.ROADS, 3)]
    
    mock_prio = MagicMock()
    mock_prio.all.return_value = [(Priority.HIGH, 4), (Priority.NORMAL, 4)]
    
    mock_status = MagicMock()
    mock_status.all.return_value = [(Status.OPEN, 6), (Status.RESOLVED, 2)]

    session.execute.side_effect = [mock_cat, mock_prio, mock_status]

    stats = await repo.aggregate_stats(session)
    assert stats["by_category"]["water"] == 5
    assert stats["by_priority"]["high"] == 4
    assert stats["by_status"]["open"] == 6
    assert stats["total"]["total"] == 8
