from datetime import datetime, timezone

from src.celery_app import celery_app
from src.core.sync_database import SyncSessionLocal as SyncSession
from src.core.sync_redis import sync_redis_client


@celery_app.task
def auto_close_expired_batches():
    from src.data.models.batch import Batch

    now = datetime.now(timezone.utc)
    with SyncSession() as session:
        expired = (
            session.query(Batch)
            .filter(
                Batch.is_closed == False,
                Batch.shift_end < now,
            )
            .all()
        )

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
        total_batches = session.query(Batch).count()
        active_batches = session.query(Batch).filter(Batch.is_closed == False).count()
        total_products = session.query(Product).count()
        aggregated_products = session.query(Product).filter(
            Product.is_aggregated == True
        ).count()

    stats = {
        "total_batches": total_batches,
        "active_batches": active_batches,
        "closed_batches": total_batches - active_batches,
        "total_products": total_products,
        "aggregated_products": aggregated_products,
        "aggregation_rate": round(
            aggregated_products / total_products * 100, 2
        ) if total_products else 0,
        "cached_at": datetime.now(timezone.utc).isoformat(),
    }

    sync_redis_client.set(
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
        failed = (
            session.query(WebhookDelivery)
            .join(WebhookSubscription)
            .filter(
                WebhookDelivery.status == "failed",
                WebhookDelivery.attempts < WebhookSubscription.retry_count,
            )
            .all()
        )

        for delivery in failed:
            send_webhook_delivery.delay(delivery.id)

    return {"retried": len(failed)}