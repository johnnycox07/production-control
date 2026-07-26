import hashlib
import hmac
import json
from datetime import datetime, timezone

import httpx
from celery import shared_task

from src.core.sync_database import SyncSessionLocal as SyncSession


@shared_task(bind=True, max_retries=3)
def send_webhook_delivery(self, delivery_id: int):
    from src.data.models.webhook import WebhookDelivery, WebhookSubscription

    with SyncSession() as session:
        delivery = session.get(WebhookDelivery, delivery_id)
        if not delivery:
            return

        subscription = session.get(WebhookSubscription, delivery.subscription_id)
        if not subscription:
            return

        payload = json.dumps(delivery.payload)

        signature = hmac.new(
            subscription.secret_key.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Event-Type": delivery.event_type,
            "X-Signature": f"sha256={signature}",
        }

        delivery.attempts += 1

        try:
            response = httpx.post(
                subscription.url,
                content=payload,
                headers=headers,
                timeout=subscription.timeout,
            )

            delivery.status = "success"
            delivery.response_status = response.status_code
            delivery.response_body = response.text[:1000]
            delivery.delivered_at = datetime.now(timezone.utc)

        except Exception as exc:
            delivery.status = "failed"
            delivery.error_message = str(exc)
            session.commit()

            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

        session.commit()