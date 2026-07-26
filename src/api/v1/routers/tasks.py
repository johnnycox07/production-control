from fastapi import APIRouter
from celery.result import AsyncResult

from src.api.v1.schemas.task import TaskStatusResponse
from src.celery_app import celery_app

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)

    return TaskStatusResponse(
        task_id=task_id,
        status=result.status,
        result=result.info if result.ready() or result.status == "PROGRESS" else None,
    )