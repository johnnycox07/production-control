from src.data.repositories.base_repository import BaseRepository
from src.data.models.webhook import WebhookSubscription, WebhookDelivery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class WebhookSubscriptionRepository(BaseRepository[WebhookSubscription]):
    def __init__(self, session: AsyncSession):
        super().__init__(WebhookSubscription, session)

    async def get_active_by_event(self, event_type: str) -> list[WebhookSubscription]:
        query = select(WebhookSubscription)
        query = query.where(
            WebhookSubscription.is_active.is_(True),
            WebhookSubscription.events.contains([event_type])
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())


class WebhookDeliveryRepository(BaseRepository[WebhookDelivery]):
    def __init__(self, session: AsyncSession):
        super().__init__(WebhookDelivery, session)

    async def get_by_subscription(
            self,
            subscription_id: int,
            offset: int = 0,
            limit: int = 20
    ) -> list[WebhookDelivery]:
        query = (
            select(WebhookDelivery)
            .where(WebhookDelivery.subscription_id == subscription_id)
            .order_by(WebhookDelivery.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_for_retry(self) -> list[WebhookDelivery]:
        query = (
            select(WebhookDelivery)
            .join(WebhookSubscription, WebhookDelivery.subscription_id == WebhookSubscription.id)
            .where(
                WebhookDelivery.status == "failed",
                WebhookDelivery.attempts < WebhookSubscription.retry_count,
            )
            .order_by(WebhookDelivery.created_at.asc())
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())