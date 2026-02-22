from datetime import datetime, timedelta, timezone

import pytest

from backend.src.infrastructure.external_services.smtp.email_client import EmailClient


@pytest.mark.requirement_id("BR-015")
@pytest.mark.test_id("TST-BR-015-WEB-UNIT-LIMIT-S2")
def test_br_015_email_client_limits_50_per_hour_for_user(monkeypatch):
    client = EmailClient()
    base_time = datetime(2026, 2, 13, 10, 0, 0, tzinfo=timezone.utc)
    step = {"i": 0}

    def fake_now():
        step["i"] += 1
        return base_time + timedelta(seconds=31 * step["i"])

    monkeypatch.setattr(client, "_now", fake_now)

    for _ in range(50):
        client.send("user@example.com", "sub", "body", {"user_id": "u-1"})

    with pytest.raises(ValueError, match="hourly send limit exceeded"):
        client.send("user@example.com", "sub", "body", {"user_id": "u-1"})


@pytest.mark.requirement_id("BR-016")
@pytest.mark.test_id("TST-BR-016-WEB-UNIT-INTERVAL-S2")
def test_br_016_email_client_requires_30_seconds_between_emails(monkeypatch):
    client = EmailClient()
    base_time = datetime(2026, 2, 13, 11, 0, 0, tzinfo=timezone.utc)
    calls = {"i": 0}

    def fake_now():
        calls["i"] += 1
        if calls["i"] == 1:
            return base_time
        return base_time + timedelta(seconds=10)

    monkeypatch.setattr(client, "_now", fake_now)

    client.send("user@example.com", "sub", "body", {"user_id": "u-2"})
    with pytest.raises(ValueError, match="minimum interval between emails is 30 seconds"):
        client.send("user@example.com", "sub", "body", {"user_id": "u-2"})


@pytest.mark.requirement_id("BR-015")
@pytest.mark.test_id("TST-BR-015-WEB-UNIT-EMAIL-FORMAT-S2")
def test_br_015_email_client_rejects_invalid_recipient():
    with pytest.raises(ValueError, match="to must be a valid email"):
        EmailClient().send("bad-recipient", "sub", "body", {"user_id": "u-3"})
