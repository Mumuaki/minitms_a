"""
Unit tests for Web-Push (FR-NOTIFY-001).
"""
import json

from pywebpush import WebPushException

from backend.src.infrastructure.api.v1.endpoints.webpush import _generate_vapid_keys
from backend.src.infrastructure.external_services.webpush.web_push_service import WebPushService


def test_generate_vapid_keys_returns_valid_pair():
    priv, pub = _generate_vapid_keys()
    assert "BEGIN PRIVATE KEY" in priv
    # P-256 uncompressed point: 65 bytes -> base64url(no padding) = 87 chars
    assert len(pub) == 87


def test_webpush_service_send_success(monkeypatch):
    captured = {}

    def fake_webpush(subscription_info, data, vapid_private_key, vapid_claims):
        captured["data"] = json.loads(data)
        captured["sub"] = subscription_info
        return None

    monkeypatch.setattr(
        "backend.src.infrastructure.external_services.webpush.web_push_service.webpush",
        fake_webpush,
    )
    service = WebPushService("PEM", "mailto:a@b.c")
    ok = service.send({"endpoint": "https://x", "keys": {}}, "T", "B")
    assert ok is True
    assert captured["data"] == {"title": "T", "body": "B"}


def test_webpush_service_send_failure(monkeypatch):
    def boom(*a, **k):
        raise WebPushException("boom")

    monkeypatch.setattr(
        "backend.src.infrastructure.external_services.webpush.web_push_service.webpush",
        boom,
    )
    service = WebPushService("PEM", "mailto:a@b.c")
    assert service.send({"endpoint": "https://x", "keys": {}}, "T", "B") is False
