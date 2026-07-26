from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.webhook import (
    WebhookSubscriptionsCreate,
    WebhookSubscriptionUpdate,
    WebhookSubscriptionResponse,
    WebhookDeliveryResponse,
)
from src.core.exceptions import WebhookNotFoundError
from src.data.repositories.webhook_repository import (
    WebhookDeliveryRepository,
    WebhookSubscriptionRepository,
)


class WebhookService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.subscription_repo = WebhookSubscriptionRepository(session)
        self.delivery_repo = WebhookDeliveryRepository(session)

    async def create_subscription(
            self, data: WebhookSubscriptionsCreate
    ) -> WebhookSubscriptionResponse:
        subscription = await self.subscription_repo.create(**data.model_dump())
        await self.session.commit()
        return WebhookSubscriptionResponse.model_validate(subscription)

    async def get_subscriptions(self) -> list[WebhookSubscriptionResponse]:
        subscriptions = await self.subscription_repo.get_all()
        return [
            WebhookSubscriptionResponse.model_validate(s)
            for s in subscriptions
        ]

    async def update_subscription(
            self, subscription_id: int, data: WebhookSubscriptionUpdate
    ) -> WebhookSubscriptionResponse:
        subscription = await self.subscription_repo.get_by_id(subscription_id)
        if subscription is None:
            raise WebhookNotFoundError(subscription_id)

        updated = await self.subscription_repo.update(
            subscription_id,
            **data.model_dump(exclude_unset=True)
        )
        await self.session.commit()
        return WebhookSubscriptionResponse.model_validate(updated)

    async def delete_subscription(self, subscription_id: int) -> None:
        subscription = await self.subscription_repo.get_by_id(subscription_id)
        if subscription is None:
            raise WebhookNotFoundError(subscription_id)
        await self.subscription_repo.delete(subscription_id)
        await self.session.commit()

    async def get_deliveries(
            self, subscription_id: int
) -> list[WebhookDeliveryResponse]:
        deliveries = await self.delivery_repo.get_by_subscription(subscription_id)
        return [WebhookDeliveryResponse.model_validate(d) for d in deliveries]

    async def send_event(self, event_type: str, payload: dict) -> None:
        subscriptions = await self.subscription_repo.get_active_by_event(event_type)

        for subscription in subscriptions:
            delivery = await self.delivery_repo.create(
                subscription_id=subscription.id,
                event_type=event_type,
                payload=payload,
                status="pending",
                attempts=0,
            )
            await self.session.commit()

            from src.tasks.webhooks import send_webhook_delivery
            send_webhook_delivery.delay(delivery.id)