import ipaddress
import socket
from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator


class WebhookSubscriptionsCreate(BaseModel):
    url: HttpUrl
    events: list[str]
    secret_key: str
    retry_count: int = 3
    timeout: int = 10

    @field_validator("url")
    @classmethod
    def no_internal_hosts(cls, v: HttpUrl) -> HttpUrl:
        host = v.host
        try:
            ip = socket.gethostbyname(host)
        except socket.gaierror:
            raise ValueError(f"Cannot resolve host: {host}")

        if ipaddress.ip_address(ip).is_private:
            raise ValueError(
                "Webhooks to internal/private addresses are not allowed"
            )
        return v


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