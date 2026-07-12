from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.celery_app import celery_app
from src.core.config import settings

sync_engine = create_engine(
    settings.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
)
SyncSession = sessionmaker(bind=sync_engine)


@celery_app.task(bind=True, max_retries=3)
def aggregate_products_batch(
    self,
    batch_id: int,
    unique_codes: list[str],
):
    from src.data.models.product import Product

    total = len(unique_codes)
    aggregated = 0
    failed = 0
    errors = []

    with SyncSession() as session:
        for i, code in enumerate(unique_codes):
            if i % 10 == 0:
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i,
                        "total": total,
                        "progress": round(i / total * 100, 1),
                    }
                )

            product_query = select(Product).where(
                Product.batch_id == batch_id,
                Product.unique_code == code,
            )

            product = session.execute(product_query).scalar_one_or_none()

            if product is None:
                failed += 1
                errors.append({"code": code, "reason": "not found"})
                continue

            if product.is_aggregated:
                failed += 1
                errors.append({"code": code, "reason": "already aggregated"})
                continue

            product.is_aggregated = True
            product.aggregated_at = datetime.now(timezone.utc)
            aggregated += 1

        session.commit()

    return {
        "success": True,
        "total": total,
        "aggregated": aggregated,
        "failed": failed,
        "errors": errors,
    }