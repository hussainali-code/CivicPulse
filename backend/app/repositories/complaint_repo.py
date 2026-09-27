import uuid
from typing import Dict, List, Optional, Tuple
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Complaint, Priority, Status


class ComplaintRepository:
    """
    Data Access Layer for Complaints.
    All SQLAlchemy queries and database interactions for complaints MUST live here.
    """

    async def create(
        self,
        session: AsyncSession,
        *,
        text: str,
        location: str,
        reporter_contact: Optional[str],
        category: Category,
        priority: Priority,
        ai_summary: Optional[str],
        triaged_by: str,
        triage_latency_ms: int,
    ) -> Complaint:
        complaint = Complaint(
            id=uuid.uuid4(),
            text=text,
            location=location,
            reporter_contact=reporter_contact,
            category=category,
            priority=priority,
            status=Status.OPEN,
            ai_summary=ai_summary,
            triaged_by=triaged_by,
            triage_latency_ms=triage_latency_ms,
        )
        session.add(complaint)
        await session.commit()
        await session.refresh(complaint)
        return complaint

    async def get_by_id(
        self,
        session: AsyncSession,
        complaint_id: uuid.UUID
    ) -> Optional[Complaint]:
        query = select(Complaint).where(Complaint.id == complaint_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def list_filtered(
        self,
        session: AsyncSession,
        *,
        category: Optional[Category] = None,
        priority: Optional[Priority] = None,
        status: Optional[Status] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Complaint], int]:
        # Base filter conditions
        conditions = []
        if category is not None:
            conditions.append(Complaint.category == category)
        if priority is not None:
            conditions.append(Complaint.priority == priority)
        if status is not None:
            conditions.append(Complaint.status == status)

        # Count query
        count_query = select(func.count(Complaint.id))
        if conditions:
            count_query = count_query.where(*conditions)
        total_count_result = await session.execute(count_query)
        total_count = total_count_result.scalar_one()

        # Data query with pagination, default newest first
        query = select(Complaint)
        if conditions:
            query = query.where(*conditions)
        
        offset = (page - 1) * page_size
        query = query.order_by(desc(Complaint.created_at)).offset(offset).limit(page_size)

        result = await session.execute(query)
        complaints = list(result.scalars().all())
        return complaints, total_count

    async def update_status(
        self,
        session: AsyncSession,
        complaint: Complaint,
        new_status: Status
    ) -> Complaint:
        complaint.status = new_status
        session.add(complaint)
        await session.commit()
        await session.refresh(complaint)
        return complaint

    async def aggregate_stats(
        self,
        session: AsyncSession
    ) -> Dict[str, Dict[str, int]]:
        # Count by category
        cat_query = select(Complaint.category, func.count(Complaint.id)).group_by(Complaint.category)
        cat_res = await session.execute(cat_query)
        by_category = {cat.value: count for cat, count in cat_res.all()}

        # Count by priority
        prio_query = select(Complaint.priority, func.count(Complaint.id)).group_by(Complaint.priority)
        prio_res = await session.execute(prio_query)
        by_priority = {prio.value: count for prio, count in prio_res.all()}

        # Count by status
        status_query = select(Complaint.status, func.count(Complaint.id)).group_by(Complaint.status)
        status_res = await session.execute(status_query)
        by_status = {st.value: count for st, count in status_res.all()}

        # Total
        total = sum(by_status.values())

        return {
            "by_category": by_category,
            "by_priority": by_priority,
            "by_status": by_status,
            "total": {"total": total},
        }

    async def get_last_triage_outcomes(
        self,
        session: AsyncSession,
        limit: int = 20
    ) -> List[Dict[str, object]]:
        query = (
            select(Complaint.triaged_by, Complaint.triage_latency_ms, Complaint.created_at)
            .order_by(desc(Complaint.created_at))
            .limit(limit)
        )
        result = await session.execute(query)
        outcomes: List[Dict[str, object]] = []
        for triaged_by, latency, created_at in result.all():
            outcomes.append({
                "provider": triaged_by,
                "latency_ms": latency,
                "fallback": "fallback" in triaged_by,
                "created_at": created_at.isoformat() if created_at else None,
            })
        return outcomes
