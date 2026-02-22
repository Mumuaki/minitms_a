from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class SyncToGoogleSheetsUseCase:
    """
    Contract-first use case for order sync to Google Sheets.
    Minimal implementation for Slice-2 TDD contract.
    """

    def execute(self, order_id: int | str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if order_id is None or str(order_id).strip() == "":
            raise ValueError("order_id is required")
        if payload is not None and not isinstance(payload, dict):
            raise ValueError("payload must be a dictionary")
        return {
            "order_id": order_id,
            "payload": payload or {},
            "status": "queued",
            "synced_at": datetime.now(timezone.utc),
        }
