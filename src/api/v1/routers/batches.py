from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.batch import BatchResponse, BatchCreate, BatchUpdate
from src.core.dependencies import get_db
from src.domain.exceptions import BatchNotFoundError
from src.domain.services.batch_service import BatchService

router = APIRouter(prefix="/batches", tags=["batches"])

async def get_batch_service(
        session: AsyncSession = Depends(get_db),
) -> BatchService:
    return BatchService(session)


@router.post("/", response_model=list[BatchResponse], status_code=201)
async def create_batches(
    data: list[BatchCreate],
    service: BatchService = Depends(get_batch_service),
):
    try:
        return await service.create_batches(data)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Batch with this number and date already exists")


@router.get("/", response_model=list[BatchResponse])
async def get_batches(
    is_closed: bool | None = None,
    batch_number: int | None = None,
    batch_date: date | None = None,
    work_center_id: int | None = None,
    shift: str | None = None,
    offset: int = 0,
    limit: int = 20,
    service: BatchService = Depends(get_batch_service),
):
    return await service.get_batches(
        is_closed=is_closed,
        batch_number=batch_number,
        batch_date=batch_date,
        work_center_id=work_center_id,
        shift=shift,
        offset=offset,
        limit=limit,
    )


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: int,
    service: BatchService = Depends(get_batch_service),
):
    try:
        return await service.get_batch(batch_id)
    except BatchNotFoundError:
        raise HTTPException(status_code=404, detail="Batch not found")


@router.patch("/{batch_id}", response_model=BatchResponse)
async def update_batch(
    batch_id: int,
    data: BatchUpdate,
    service: BatchService = Depends(get_batch_service),
):
    try:
        return await service.update_batch(batch_id, data)
    except BatchNotFoundError:
        raise HTTPException(status_code=404, detail="Batch not found")
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Batch with this number and date already exists")
