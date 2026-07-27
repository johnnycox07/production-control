import asyncio
import os
import tempfile
import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.batch import AsyncAggregateRequest
from src.api.v1.schemas.batch import BatchResponse, BatchCreate, BatchUpdate
from src.api.v1.schemas.batch import ExportRequest
from src.api.v1.schemas.product import ProductResponse, AggregateRequest
from src.api.v1.schemas.task import TaskResponse
from src.core.dependencies import get_db
from src.core.dependencies import service_factory
from src.domain.services.batch_service import BatchService
from src.domain.services.product_service import ProductService
from src.storage.minio_service import MinIOService
from src.tasks.aggregation import aggregate_products_batch
from src.tasks.exports import export_batches_to_file
from src.tasks.imports import import_batches_from_file

router = APIRouter(prefix="/batches", tags=["batches"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

BatchServiceDep = Annotated[
    BatchService,
    Depends(service_factory(BatchService)),
]

@router.post("/", response_model=list[BatchResponse], status_code=201)
async def create_batches(
    data: list[BatchCreate],
    service: BatchServiceDep,
):
    try:
        return await service.create_batches(data)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Batch with this number and date already exists")


@router.get("/", response_model=list[BatchResponse])
async def get_batches(
    service: BatchServiceDep,
    is_closed: bool | None = None,
    batch_number: int | None = None,
    batch_date: date | None = None,
    work_center_id: int | None = None,
    shift: str | None = None,
    offset: int = 0,
    limit: int = 20,
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
    service: BatchServiceDep,
):
    return await service.get_batch(batch_id)


@router.patch("/{batch_id}", response_model=BatchResponse)
async def update_batch(
    batch_id: int,
    data: BatchUpdate,
    service: BatchServiceDep,
):
    try:
        return await service.update_batch(batch_id, data)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Batch with this number and date already exists")


@router.post(
    "/{batch_id}/aggregate",
    response_model=ProductResponse,
    summary="Агрегировать один продукт",
    description=(
        "Синхронная агрегация одного продукта по unique_code. "
        "Используй когда нужно агрегировать единичный продукт и получить результат немедленно."
    ),
)
async def aggregate_product(
        batch_id: int,
        data: AggregateRequest,
        session: AsyncSession = Depends(get_db)
):
    service = ProductService(session)
    return await service.aggregate_product(batch_id, data.unique_code)


@router.post(
    "/{batch_id}/aggregate-async",
    response_model=TaskResponse,
    status_code=202,
    summary="Массовая агрегация продукции",
    description=(
        "Асинхронная агрегация списка продуктов через Celery. "
        "Используй когда нужно агрегировать >100 единиц. "
        "Возвращает task_id — статус проверяй через GET /tasks/{task_id}."
    ),
)
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
    # Проверка расширения
    safe_ext = os.path.splitext(file.filename or "")[1].lower()
    if safe_ext not in (".xlsx", ".xls"):
        raise HTTPException(status_code=400, detail="Unsupported file type. Only .xlsx and .xls allowed.")

    # Читаем с лимитом размера
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")

    # Генерируем безопасное имя — без user input в object_name
    object_name = f"import_{uuid.uuid4().hex}{safe_ext}"

    def _save_and_upload() -> str:
        with tempfile.NamedTemporaryFile(suffix=safe_ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        minio = MinIOService()
        minio.upload_file("imports", tmp_path, object_name)
        os.unlink(tmp_path)
        return object_name

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _save_and_upload)

    task = import_batches_from_file.delay(object_name)
    return TaskResponse(
        task_id=task.id,
        status="PENDING",
        message="File uploaded, import started",
    )


@router.post("/export", response_model=TaskResponse, status_code=202)
async def export_batches(data: ExportRequest):
    task = export_batches_to_file.delay(data.filters.model_dump(mode="json"), data.format)
    return TaskResponse(
        task_id=task.id,
        status="PENDING",
        message="Export started",
    )