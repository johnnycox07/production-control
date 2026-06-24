from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from ...core.database import Base


class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    url: Mapped[str] = mapped_column(
        nullable=False,
    )

    events: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
    )

    secret_key: Mapped[str] = mapped_column(
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
    )

    retry_count: Mapped[int] = mapped_column(
        default=3,
    )

    timeout: Mapped[int] = mapped_column(
        default=10,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        back_populates="subscription",
    )


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("webhook_subscriptions.id"),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        nullable=False,
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        nullable=False,
    )

    attempts: Mapped[int] = mapped_column(
        default=0,
    )

    response_status: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    response_body: Mapped[str | None] = mapped_column(
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    delivered_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )

    subscription: Mapped["WebhookSubscription"] = relationship(
        back_populates="deliveries",
    )