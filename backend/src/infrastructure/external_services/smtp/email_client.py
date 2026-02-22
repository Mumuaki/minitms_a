from __future__ import annotations

from datetime import datetime, timezone
from collections import defaultdict, deque
from typing import Any


class EmailClient:
    """
    Contract-first SMTP client.
    Minimal implementation for Slice-2 TDD contract.
    """

    def __init__(self) -> None:
        self._send_history: dict[str, deque[datetime]] = defaultdict(deque)

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def send(self, to: str, subject: str, body: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        if "@" not in to:
            raise ValueError("to must be a valid email")
        if not subject.strip():
            raise ValueError("subject is required")
        if not body.strip():
            raise ValueError("body is required")

        metadata = metadata or {}
        user_id = str(metadata.get("user_id", "")).strip()
        now = self._now()

        if user_id:
            history = self._send_history[user_id]
            one_hour_ago = now.timestamp() - 3600
            while history and history[0].timestamp() < one_hour_ago:
                history.popleft()

            if len(history) >= 50:
                raise ValueError("hourly send limit exceeded")

            if history and (now - history[-1]).total_seconds() < 30:
                raise ValueError("minimum interval between emails is 30 seconds")

            history.append(now)

        return {
            "to": to,
            "subject": subject,
            "body": body,
            "metadata": metadata,
            "sent_at": now,
            "status": "accepted",
        }
