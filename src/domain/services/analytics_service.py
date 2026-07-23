import json
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import cache
from src.core.exceptions import BatchNotFoundError
from src.data.models.batch import Batch
from src.data.models.product import Product


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_dashboard_statistics(self) -> dict:
        cached = await cache.get("dashboard_stats")
        if cached:
            return json.loads(cached)

        total_batches = await self.session.scalar(
            select(func.count(Batch.id))
        )
        active_batches = await self.session.scalar(
            select(func.count(Batch.id)).where(Batch.is_closed.is_(False))
        )
        total_products = await self.session.scalar(
            select(func.count(Product.id))
        )
        aggregated_products = await self.session.scalar(
            select(func.count(Product.id)).where(Product.is_aggregated.is_(True))
        )

        stats = {
            "summary": {
                "total_batches": total_batches or 0,
                "active_batches": active_batches or 0,
                "closed_batches": (total_batches or 0) - (active_batches or 0),
                "total_products": total_products or 0,
                "aggregated_products": aggregated_products or 0,
                "aggregation_rate": round(
                    (aggregated_products or 0) / (total_products or 1) * 100, 2
                ),
            },
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }

        await cache.set("dashboard_stats", json.dumps(stats), ttl=300)

        return stats

    async def get_batch_statistics(self, batch_id: int) -> dict:
        key = f"batch_statistics:{batch_id}"
        cached = await cache.get(key)
        if cached:
            return json.loads(cached)

        batch = await self.session.get(Batch, batch_id)

        if batch is None:
            raise BatchNotFoundError(batch_id)

        total = await self.session.scalar(
            select(func.count(Product.id)).where(Product.batch_id == batch_id)
        )
        aggregated = await self.session.scalar(
            select(func.count(Product.id)).where(
                Product.batch_id == batch_id,
                Product.is_aggregated.is_(True),
            )
        )

        total = total or 0
        aggregated = aggregated or 0
        remaining = total - aggregated

        shift_duration = (
            batch.shift_end - batch.shift_start
        ).total_seconds() / 3600  # в часах

        products_per_hour = round(
            aggregated / shift_duration, 2
        ) if shift_duration > 0 else 0

        stats = {
            "batch_info": {
                "id": batch.id,
                "batch_number": batch.batch_number,
                "batch_date": str(batch.batch_date),
                "is_closed": batch.is_closed,
            },
            "production_stats": {
                "total_products": total,
                "aggregated": aggregated,
                "remaining": remaining,
                "aggregation_rate": round(
                    aggregated / total * 100, 2
                ) if total > 0 else 0,
            },
            "timeline": {
                "shift_duration_hours": round(shift_duration, 2),
                "products_per_hour": products_per_hour,
            },
        }

        await cache.set(key, json.dumps(stats), ttl=300)
        return stats

    async def compare_batches(self, batch_ids: list[int]) -> dict:
        batch_query = (
            select(Batch)
            .where(Batch.id.in_(batch_ids))
        )

        batches = (
            await self.session.execute(batch_query)
        ).scalars().all()

        product_stats_query = (
            select(
                Product.batch_id,
                func.count(Product.id).label("total"),
                func.count(Product.id)
                .filter(Product.is_aggregated.is_(True))
                .label("aggregated"),
            )
            .where(Product.batch_id.in_(batch_ids))
            .group_by(Product.batch_id)
        )

        product_stats = (
            await self.session.execute(product_stats_query)
        ).all()

        stats_map = {
            row.batch_id: row
            for row in product_stats
        }

        comparison = []

        for batch in batches:
            stats = stats_map.get(batch.id)

            total = stats.total if stats else 0
            aggregated = stats.aggregated if stats else 0

            shift_hours = (
                  batch.shift_end - batch.shift_start
            ).total_seconds() / 3600

            comparison.append({
                "batch_id": batch.id,
                "batch_number": batch.batch_number,
                "total_products": total,
                "aggregated": aggregated,
                "rate": round(
                    aggregated / total * 100,
                    2,
                ) if total > 0 else 0,
                "duration_hours": round(shift_hours, 2),
                "products_per_hour": round(
                    aggregated / shift_hours,
                    2,
                ) if shift_hours > 0 else 0,
            })

        if comparison:
            avg_rate = round(
                sum(item["rate"] for item in comparison) / len(comparison),
                2,
            )
            avg_per_hour = round(
                sum(item["products_per_hour"] for item in comparison) / len(comparison),
                2,
            )
        else:
            avg_rate = 0
            avg_per_hour = 0

        return {
            "comparison": comparison,
            "average": {
                "aggregation_rate": avg_rate,
                "products_per_hour": avg_per_hour,
            },
        }