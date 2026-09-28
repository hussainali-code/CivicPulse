import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.models import Category, Complaint, Priority, Status
from app.providers.triage.base import TriageResult
from app.services.complaint_service import (
    ComplaintNotFoundException,
    ComplaintService,
    InvalidStateTransitionException,
)


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    return ComplaintService(repo=mock_repo)


@pytest.mark.asyncio
async def test_create_complaint_orchestrates_triage_and_repo(service, mock_repo):
    session = AsyncMock()
    mock_provider = AsyncMock()
    mock_provider.name = "simulated"
    mock_provider.triage.return_value = TriageResult(
        category=Category.WATER,
        priority=Priority.HIGH,
        summary="Water pipe burst on main road.",
        confidence=0.95,
    )

    created_complaint = Complaint(
        id=uuid.uuid4(),
        text="Water pipe burst on main road in Sector F-7.",
        location="Sector F-7",
        reporter_contact="test@example.com",
        category=Category.WATER,
        priority=Priority.HIGH,
        status=Status.OPEN,
        ai_summary="Water pipe burst on main road.",
        triaged_by="simulated",
        triage_latency_ms=10,
    )
    mock_repo.create.return_value = created_complaint

    with patch.object(service, "invalidate_stats_cache", new_callable=AsyncMock) as mock_invalidate:
        res = await service.create_complaint(
            session,
            mock_provider,
            text="Water pipe burst on main road in Sector F-7.",
            location="Sector F-7",
            reporter_contact="test@example.com",
        )

        assert res.id == created_complaint.id
        assert res.category == Category.WATER
        assert res.priority == Priority.HIGH
        mock_provider.triage.assert_awaited_once_with(
            "Water pipe burst on main road in Sector F-7.", "Sector F-7"
        )
        mock_repo.create.assert_awaited_once()
        mock_invalidate.assert_awaited_once()


@pytest.mark.asyncio
async def test_valid_state_transitions(service, mock_repo):
    session = AsyncMock()
    cid = uuid.uuid4()

    valid_cases = [
        (Status.OPEN, Status.IN_PROGRESS),
        (Status.OPEN, Status.REJECTED),
        (Status.IN_PROGRESS, Status.RESOLVED),
        (Status.IN_PROGRESS, Status.REJECTED),
    ]

    for current_st, new_st in valid_cases:
        mock_complaint = Complaint(
            id=cid,
            text="Some issue reported here",
            location="Test Area",
            reporter_contact=None,
            category=Category.ROADS,
            priority=Priority.NORMAL,
            status=current_st,
            triaged_by="simulated",
            triage_latency_ms=5,
        )
        mock_repo.get_by_id.return_value = mock_complaint
        mock_repo.update_status.return_value = mock_complaint

        with patch.object(service, "invalidate_stats_cache", new_callable=AsyncMock):
            await service.update_complaint_status(session, cid, new_st)
            mock_repo.update_status.assert_awaited_with(session, mock_complaint, new_st)


@pytest.mark.asyncio
async def test_invalid_state_transitions_raise_exact_message(service, mock_repo):
    session = AsyncMock()
    cid = uuid.uuid4()

    invalid_cases = [
        (Status.RESOLVED, Status.OPEN),
        (Status.RESOLVED, Status.IN_PROGRESS),
        (Status.REJECTED, Status.OPEN),
        (Status.REJECTED, Status.IN_PROGRESS),
        (Status.OPEN, Status.RESOLVED),
    ]

    for current_st, new_st in invalid_cases:
        mock_complaint = Complaint(
            id=cid,
            text="Some issue reported here",
            location="Test Area",
            reporter_contact=None,
            category=Category.ROADS,
            priority=Priority.NORMAL,
            status=current_st,
            triaged_by="simulated",
            triage_latency_ms=5,
        )
        mock_repo.get_by_id.return_value = mock_complaint

        with pytest.raises(InvalidStateTransitionException) as exc_info:
            await service.update_complaint_status(session, cid, new_st)

        assert str(exc_info.value) == f"cannot transition from {current_st.value} to {new_st.value}"


@pytest.mark.asyncio
async def test_get_complaint_not_found_raises_exception(service, mock_repo):
    session = AsyncMock()
    cid = uuid.uuid4()
    mock_repo.get_by_id.return_value = None

    with pytest.raises(ComplaintNotFoundException) as exc_info:
        await service.get_complaint(session, cid)

    assert f"complaint with id {cid} not found" in str(exc_info.value)
