from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.core.dependencies import service_factory
from src.core.exceptions import BatchNotFoundError
from src.domain.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

AnalyticsServiceDep = Annotated[
    AnalyticsService,
    Depends(service_factory(AnalyticsService))
]

@router.get("/dashboard")
async def get_dashboard(
    service: AnalyticsServiceDep,
):
    return await service.get_dashboard_statistics()


@router.get("/batches/{batch_id}/statistics")
async def get_batch_statistics(
    batch_id: int,
    service: AnalyticsServiceDep,
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
    service: AnalyticsServiceDep,
):
    return await service.compare_batches(data.batch_ids)