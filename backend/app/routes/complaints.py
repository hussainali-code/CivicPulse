import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models import Category, Priority, Status
from app.providers.triage.base import TriageProvider
from app.providers.triage.factory import get_triage_provider
from app.schemas import (
    ComplaintCreate,
    ComplaintListResponse,
    ComplaintResponse,
    StatusPatch,
)
from app.services.complaint_service import (
    ComplaintNotFoundException,
    ComplaintService,
    InvalidStateTransitionException,
    get_complaint_service,
)

router = APIRouter()


@router.post(
    "/complaints",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new citizen complaint",
)
async def create_complaint(
    payload: ComplaintCreate,
    service: ComplaintService = Depends(get_complaint_service),
    provider: TriageProvider = Depends(get_triage_provider),
) -> ComplaintResponse:
    complaint = await service.create(
        provider,
        text=payload.text,
        location=payload.location,
        reporter_contact=payload.reporter_contact,
    )
    return ComplaintResponse.model_validate(complaint)


@router.get(
    "/complaints",
    response_model=ComplaintListResponse,
    status_code=status.HTTP_200_OK,
    summary="List paginated complaints with optional filtering",
)
async def list_complaints(
    category: Optional[Category] = Query(default=None, description="Filter by category"),
    priority: Optional[Priority] = Query(default=None, description="Filter by priority"),
    complaint_status: Optional[Status] = Query(default=None, alias="status", description="Filter by status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintListResponse:
    items, total = await service.list_all(
        category=category,
        priority=priority,
        status=complaint_status,
        page=page,
        page_size=page_size,
    )
    return ComplaintListResponse(
        items=[ComplaintResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/complaints/{id}",
    response_model=ComplaintResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a complaint by UUID",
)
async def get_complaint(
    id: uuid.UUID,
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintResponse:
    try:
        complaint = await service.get_by_id(id)
        return ComplaintResponse.model_validate(complaint)
    except ComplaintNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.patch(
    "/complaints/{id}/status",
    response_model=ComplaintResponse,
    status_code=status.HTTP_200_OK,
    summary="Transition complaint status according to explicit state machine",
)
async def update_complaint_status(
    id: uuid.UUID,
    payload: StatusPatch,
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintResponse:
    try:
        updated = await service.update_status(id, payload.status)
        return ComplaintResponse.model_validate(updated)
    except ComplaintNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except InvalidStateTransitionException as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
