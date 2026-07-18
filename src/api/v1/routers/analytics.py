from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db
from src.domain.exceptions import BatchNotFoundError
from src.domain.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


async def get_analytics_service(
    session: AsyncSession = Depends(get_db),
) -> AnalyticsService:
    return AnalyticsService(session)


@router.get("/dashboard")
async def get_dashboard(
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.get_dashboard_statistics()


@router.get("/batches/{batch_id}/statistics")
async def get_batch_statistics(
    batch_id: int,
    service: AnalyticsService = Depends(get_analytics_service),
):
    try:
        return await service.get_batch_statistics(batch_id)
    except BatchNotFoundError:
        raise HTTPException(status_code=404, detail="Batch not found")

class CompareBatchesRequest(BaseModel):
    batch_ids: list[int]

    
@router.post("/batches/compare")
async def compare_batches(
    data: CompareBatchesRequest,
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.compare_batches(data.batch_ids)