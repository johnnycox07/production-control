from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.api.v1.schemas.webhook import (
    WebhookSubscriptionsCreate,
    WebhookSubscriptionUpdate,
    WebhookSubscriptionResponse,
    WebhookDeliveryResponse,
)
from src.core.dependencies import service_factory
from src.domain.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

WebhookServiceDep = Annotated[
    WebhookService,
    Depends(service_factory(WebhookService)),
]


@router.post("/", response_model=WebhookSubscriptionResponse, status_code=201)
async def create_subscription(
    data: WebhookSubscriptionsCreate,
    service: WebhookServiceDep,
):
    return await service.create_subscription(data)


@router.get("/", response_model=list[WebhookSubscriptionResponse])
async def get_subscriptions(
    service: WebhookServiceDep,
):
    return await service.get_subscriptions()


@router.patch("/{webhook_id}", response_model=WebhookSubscriptionResponse)
async def update_subscription(
    webhook_id: int,
    data: WebhookSubscriptionUpdate,
    service: WebhookServiceDep,
):
    return await service.update_subscription(webhook_id, data)


@router.delete("/{webhook_id}", status_code=204)
async def delete_subscription(
    webhook_id: int,
    service: WebhookServiceDep,
):
    await service.delete_subscription(webhook_id)


@router.get(
    "/{webhook_id}/deliveries",
    response_model=list[WebhookDeliveryResponse],
)
async def get_deliveries(
    webhook_id: int,
    service: WebhookServiceDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    return await service.get_deliveries(
        subscription_id=webhook_id,
        offset=offset,
        limit=limit,
    )