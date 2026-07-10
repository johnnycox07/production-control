from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.webhook import (
    WebhookSubscriptionsCreate,
    WebhookSubscriptionUpdate,
    WebhookSubscriptionResponse,
    WebhookDeliveryResponse,
)
from src.core.dependencies import get_db
from src.domain.exceptions import WebhookNotFoundError
from src.domain.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


async def get_webhook_service(
    session: AsyncSession = Depends(get_db),
) -> WebhookService:
    return WebhookService(session)


@router.post("/", response_model=WebhookSubscriptionResponse, status_code=201)
async def create_subscription(
    data: WebhookSubscriptionsCreate,
    service: WebhookService = Depends(get_webhook_service),
):
    return await service.create_subscription(data)


@router.get("/", response_model=list[WebhookSubscriptionResponse])
async def get_subscriptions(
    service: WebhookService = Depends(get_webhook_service),
):
    return await service.get_subscriptions()


@router.patch("/{webhook_id}", response_model=WebhookSubscriptionResponse)
async def update_subscription(
    webhook_id: int,
    data: WebhookSubscriptionUpdate,
    service: WebhookService = Depends(get_webhook_service),
):
    try:
        return await service.update_subscription(webhook_id, data)
    except WebhookNotFoundError:
        raise HTTPException(status_code=404, detail="Webhook not found")


@router.delete("/{webhook_id}", status_code=204)
async def delete_subscription(
    webhook_id: int,
    service: WebhookService = Depends(get_webhook_service),
):
    try:
        await service.delete_subscription(webhook_id)
    except WebhookNotFoundError:
        raise HTTPException(status_code=404, detail="Webhook not found")


@router.get(
    "/{webhook_id}/deliveries",
    response_model=list[WebhookDeliveryResponse],
)
async def get_deliveries(
    webhook_id: int,
    service: WebhookService = Depends(get_webhook_service),
):
    return await service.get_deliveries(webhook_id)