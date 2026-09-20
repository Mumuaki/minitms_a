"""Web-Push отправка через pywebpush (FR-NOTIFY-001)."""
import json
import logging

from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)


class WebPushService:
    """Отправляет push-уведомление в браузер по Web Push (RFC 8030 / VAPID)."""

    def __init__(self, vapid_private_key: str, vapid_claims_sub: str = "mailto:admin@minitms.local"):
        self._private_key = vapid_private_key
        self._claims = {"sub": vapid_claims_sub}

    def send(self, subscription: dict, title: str, body: str) -> bool:
        try:
            payload = json.dumps({"title": title, "body": body})
            webpush(
                subscription_info=subscription,
                data=payload,
                vapid_private_key=self._private_key,
                vapid_claims=self._claims,
            )
            return True
        except WebPushException as e:
            logger.warning("WebPush send failed: %s", e)
            return False
        except Exception as e:
            logger.warning("WebPush send unexpected error: %s", e)
            return False
