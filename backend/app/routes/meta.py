from fastapi import APIRouter, Depends, status

from app.config import get_settings
from app.schemas import ProvidersMetaResponse, TriageOutcomeItem
from app.services.complaint_service import ComplaintService, get_complaint_service

router = APIRouter()
settings = get_settings()


@router.get(
    "/meta/providers",
    response_model=ProvidersMetaResponse,
    status_code=status.HTTP_200_OK,
    summary="Observability endpoint returning active triage provider and last 20 triage outcomes",
)
async def get_providers_meta(
    service: ComplaintService = Depends(get_complaint_service),
) -> ProvidersMetaResponse:
    outcomes_data = await service.get_last_triage_outcomes(limit=20)
    outcomes = [
        TriageOutcomeItem(
            provider=str(item.get("provider", "")),
            latency_ms=int(str(item.get("latency_ms", 0))),
            fallback=bool(item.get("fallback", False)),
            created_at=str(item.get("created_at")) if item.get("created_at") else None,
        )
        for item in outcomes_data
    ]
    return ProvidersMetaResponse(
        active_provider=settings.TRIAGE_PROVIDER,
        outcomes=outcomes,
    )
