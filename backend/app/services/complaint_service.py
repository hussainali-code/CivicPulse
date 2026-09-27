import time
import uuid
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Complaint, Priority, Status
from app.providers.cache import get_redis_client
from app.providers.triage.base import TriageProvider, TriageResult
from app.repositories.complaint_repo import ComplaintRepository


class ComplaintNotFoundException(Exception):
    def __init__(self, complaint_id: uuid.UUID):
        self.complaint_id = complaint_id
        super().__init__(f"complaint with id {complaint_id} not found")


class InvalidStateTransitionException(Exception):
    def __init__(self, current_status: Status, new_status: Status):
        self.current_status = current_status
        self.new_status = new_status
        super().__init__(f"cannot transition from {current_status.value} to {new_status.value}")


VALID_TRANSITIONS = {
    (Status.OPEN, Status.IN_PROGRESS),
    (Status.OPEN, Status.REJECTED),
    (Status.IN_PROGRESS, Status.RESOLVED),
    (Status.IN_PROGRESS, Status.REJECTED),
}


class ComplaintService:
    def __init__(
        self,
        repo: Optional[ComplaintRepository] = None,
    ):
        self.repo = repo or ComplaintRepository()

    async def invalidate_stats_cache(self) -> None:
        """Invalidate the cached statistics in Redis."""
        try:
            client = get_redis_client()
            await client.delete("civicpulse:stats")
        except Exception:
            # Cache failure should not block core transaction
            pass

    async def create_complaint(
        self,
        session: AsyncSession,
        triage_provider: TriageProvider,
        *,
        text: str,
        location: str,
        reporter_contact: Optional[str] = None,
    ) -> Complaint:
        # Run AI triage with latency timing
        start_time = time.perf_counter()
        triage_result: TriageResult = await triage_provider.triage(text, location)
        duration = time.perf_counter() - start_time
        latency_ms = max(1, int(duration * 1000))

        # Persist through repository
        complaint = await self.repo.create(
            session,
            text=text,
            location=location,
            reporter_contact=reporter_contact,
            category=triage_result.category,
            priority=triage_result.priority,
            ai_summary=triage_result.summary,
            triaged_by=triage_provider.name,
            triage_latency_ms=latency_ms,
        )

        # Invalidate stats cache
        await self.invalidate_stats_cache()

        return complaint

    async def get_complaint(
        self,
        session: AsyncSession,
        complaint_id: uuid.UUID
    ) -> Complaint:
        complaint = await self.repo.get_by_id(session, complaint_id)
        if complaint is None:
            raise ComplaintNotFoundException(complaint_id)
        return complaint

    async def list_complaints(
        self,
        session: AsyncSession,
        *,
        category: Optional[Category] = None,
        priority: Optional[Priority] = None,
        status: Optional[Status] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Complaint], int]:
        return await self.repo.list_filtered(
            session,
            category=category,
            priority=priority,
            status=status,
            page=page,
            page_size=page_size,
        )

    async def update_complaint_status(
        self,
        session: AsyncSession,
        complaint_id: uuid.UUID,
        new_status: Status
    ) -> Complaint:
        complaint = await self.get_complaint(session, complaint_id)

        # Enforce state transition rules
        transition = (complaint.status, new_status)
        if transition not in VALID_TRANSITIONS:
            raise InvalidStateTransitionException(complaint.status, new_status)

        updated = await self.repo.update_status(session, complaint, new_status)

        # Invalidate stats cache
        await self.invalidate_stats_cache()

        return updated
