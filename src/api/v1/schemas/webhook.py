from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WebhookSubscriptionsCreate(BaseModel):
    url: str
    events: list[str]
    secret_key: str
    retry_count: int
    timeout: int


class WebhookSubscriptionUpdate(BaseModel):
    url: str | None = None
    events: list[str] | None = None
    is_active: bool | None = None
    retry_count: int | None = None
    timeout: int | None = None


class WebhookSubscriptionResponse(BaseModel):
    id: int
    url: str
    events: list[str]
    is_active: bool
    retry_count: int
    timeout: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookDeliveryResponse(BaseModel):
    id: int
    subscription_id: int
    event_type: str
    payload: dict
    status: str
    attempts: int
    response_status: int | None
    response_body: str | None
    error_message: str | None
    created_at: datetime
    delivered_at: datetime | None

    model_config = ConfigDict(from_attributes=True)