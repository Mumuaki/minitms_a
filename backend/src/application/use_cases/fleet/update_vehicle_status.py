from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.src.domain.entities.vehicle import VehicleStatus


class UpdateVehicleStatusUseCase:
    """
    Contract-first use case for vehicle status updates.
    Minimal implementation for Slice-2 TDD contract.
    """

    def execute(self, vehicle_id: int | str, status: str, actor_id: int | str | None = None) -> dict[str, Any]:
        if vehicle_id is None or str(vehicle_id).strip() == "":
            raise ValueError("vehicle_id is required")
        if status not in {item.value for item in VehicleStatus}:
            raise ValueError("status must be a valid VehicleStatus value")
        return {
            "vehicle_id": vehicle_id,
            "status": status,
            "actor_id": actor_id,
            "updated_at": datetime.now(timezone.utc),
        }
