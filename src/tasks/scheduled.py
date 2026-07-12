from datetime import datetime, timezone

import redis
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from src.celery_app import celery_app
from src.core.config import settings

sync_engine = create_engine(
    settings.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
)
SyncSession = sessionmaker(bind=sync_engine, expire_on_commit=False)


@celery_app.task
def auto_close_expired_batches():
    from src.data.models.batch import Batch

    now = datetime.now(timezone.utc)
    with SyncSession() as session:
        expired_query = select(Batch).where(
            Batch.is_closed.is_(False),
            Batch.shift_end < now,
        )

        expired = session.execute(expired_query).scalars().all()

        for batch in expired:
            batch.is_closed = True
            batch.closed_at = now

        session.commit()

    return {"closed": len(expired)}


@celery_app.task
def cleanup_old_files():
    from src.storage.minio_service import MinIOService
    from datetime import timedelta

    minio = MinIOService()
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    deleted = 0

    for bucket in ["reports", "exports", "imports"]:
        for obj in minio.list_files(bucket):
            if obj.last_modified < cutoff:
                minio.delete_file(bucket, obj.object_name)
                deleted += 1

    return {"deleted": deleted}


@celery_app.task
def update_cached_statistics():
    import json

    from src.data.models.batch import Batch
    from src.data.models.product import Product

    with SyncSession() as session:
        total_batches = session.scalar(
            select(func.count()).select_from(Batch)
        )

        active_batches = session.scalar(
            select(func.count())
            .select_from(Batch)
            .where(Batch.is_closed.is_(False))
        )

        total_products = session.scalar(
            select(func.count()).select_from(Product)
        )

        aggregated_products = session.scalar(
            select(func.count())
            .select_from(Product)
            .where(Product.is_aggregated.is_(True))
        )

    stats = {
        "total_batches": total_batches,
        "active_batches": active_batches,
        "closed_batches": total_batches - active_batches,
        "total_products": total_products,
        "aggregated_products": aggregated_products,
        "aggregation_rate": round(
            aggregated_products / total_products * 100,
            2,
        ) if total_products else 0,
        "cached_at": datetime.now(timezone.utc).isoformat(),
    }

    redis_client = redis.from_url(settings.redis_url)

    redis_client.set(
        "dashboard_stats",
        json.dumps(stats),
        ex=300,
    )

    return stats


@celery_app.task
def retry_failed_webhooks():
    from src.data.models.webhook import WebhookDelivery, WebhookSubscription
    from src.tasks.webhooks import send_webhook_delivery

    with SyncSession() as session:
        failed_query = (
            select(WebhookDelivery)
            .join(WebhookSubscription)
            .where(
                WebhookDelivery.status == "failed",
                WebhookDelivery.attempts < WebhookSubscription.retry_count,
            )
        )

        failed = session.execute(failed_query).scalars().all()

        for delivery in failed:
            send_webhook_delivery.delay(delivery.id)

    return {"retried": len(failed)}