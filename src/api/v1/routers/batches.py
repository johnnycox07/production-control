import os
import tempfile
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.batch import AsyncAggregateRequest
from src.api.v1.schemas.batch import BatchResponse, BatchCreate, BatchUpdate
from src.api.v1.schemas.product import ProductResponse, AggregateRequest
from src.api.v1.schemas.task import TaskResponse
from src.core.dependencies import get_db
from src.domain.exceptions import BatchNotFoundError, ProductNotFoundError, ProductAlreadyAggregatedError
from src.domain.services.batch_service import BatchService
from src.domain.services.product_service import ProductService
from src.storage.minio_service import MinIOService
from src.tasks.aggregation import aggregate_products_batch
from src.tasks.exports import export_batches_to_file
from src.tasks.imports import import_batches_from_file

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


@router.post("/{batch_id}/aggregate", response_model=ProductResponse)
async def aggregate_product(
        batch_id: int,
        data: AggregateRequest,
        session: AsyncSession = Depends(get_db)
):
    service = ProductService(session)
    try:
        return await service.aggregate_product(batch_id, data.unique_code)
    except ProductNotFoundError:
        raise HTTPException(status_code=404, detail="Product not found")
    except ProductAlreadyAggregatedError:
        raise HTTPException(status_code=409, detail="Product already aggregated")


@router.post("/{batch_id}/aggregate-async", response_model=TaskResponse, status_code=202)
async def aggregate_products_async(
    batch_id: int,
    data: AsyncAggregateRequest,
):
    task = aggregate_products_batch.delay(batch_id, data.unique_codes)
    return TaskResponse(
        task_id=task.id,
        status="PENDING",
        message="Aggregation task started",
    )


# --- Import / Export ---

@router.post("/import", response_model=TaskResponse, status_code=202)
async def import_batches(file: UploadFile = File(...)):
    minio = MinIOService()

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    object_name = f"import_{file.filename}"
    minio.upload_file("imports", tmp_path, object_name)
    os.unlink(tmp_path)

    task = import_batches_from_file.delay(object_name)
    return TaskResponse(
        task_id=task.id,
        status="PENDING",
        message="File uploaded, import started",
    )


class ExportRequest(BaseModel):
    format: str = "excel"
    filters: dict = {}


@router.post("/export", response_model=TaskResponse, status_code=202)
async def export_batches(data: ExportRequest):
    task = export_batches_to_file.delay(data.filters, data.format)
    return TaskResponse(
        task_id=task.id,
        status="PENDING",
        message="Export started",
    )