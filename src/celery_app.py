from celery import Celery

from src.core.config import settings

celery_app = Celery(
    "production_control",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.tasks.aggregation",
        "src.tasks.reports",
        "src.tasks.imports",
        "src.tasks.exports",
        "src.tasks.webhooks",
        "src.tasks.scheduled",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    timezone="UTC",
    enable_utc=True,

    result_expires=86400,

    task_acks_late=True,
)

celery_app.conf.beat_schedule = {
    "auto-close-expired-batches": {
        "task": "src.tasks.scheduled.auto_close_expired_batches",
        "schedule": 3600.0,
    },
    "cleanup-old-files": {
        "task": "src.tasks.scheduled.cleanup_old_files",
        "schedule": 86400.0,
    },
    "update-statistics": {
        "task": "src.tasks.scheduled.update_cached_statistics",
        "schedule": 300.0,  
    },
    "retry-failed-webhooks": {
        "task": "src.tasks.scheduled.retry_failed_webhooks",
        "schedule": 900.0,
    },
}