from fastapi import APIRouter, Depends, Response, status

from app.schemas import StatsResponse
from app.services.stats_service import StatsService, get_stats_service

router = APIRouter()


@router.get(
    "/stats",
    response_model=StatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregated complaint statistics with Redis read-through caching",
)
async def get_stats(
    response: Response,
    service: StatsService = Depends(get_stats_service),
) -> StatsResponse:
    stats_data, cache_status = await service.get_stats()
    response.headers["X-Cache"] = cache_status
    return StatsResponse(
        by_category=stats_data.get("by_category", {}),
        by_priority=stats_data.get("by_priority", {}),
        by_status=stats_data.get("by_status", {}),
        total=stats_data.get("total", {"total": 0}),
    )
