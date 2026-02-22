"""Refresh vehicle current_location from GPS (Dozor first, then Guard, then mock)."""
import json
import os
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.src.application.dto.vehicle_dto import VehicleResponse
from backend.src.infrastructure.persistence.sqlalchemy.repositories.vehicle_repository_impl import VehicleRepositoryImpl
from backend.src.infrastructure.external_services.gps.dozor_gps_adapter import DozorGpsAdapter
from backend.src.infrastructure.external_services.gps.gps_guard_adapter import GpsGuardAdapter
from backend.src.infrastructure.external_services.gps.mock_gps_service import MockGpsService


# #region agent log
def _debug_log_refresh(msg: str, data: dict, hypothesis_id: str) -> None:
    try:
        path = os.environ.get("DEBUG_LOG_PATH", "/app/debug-fa2d8a.log" if os.path.exists("/app") else "debug-fa2d8a.log")
        payload = {"sessionId": "fa2d8a", "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000), "location": "refresh_vehicle_location", "message": msg, "data": data, "hypothesisId": hypothesis_id}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
# #endregion


class RefreshVehicleLocationUseCase:
    def __init__(self, db: Session):
        self.repository = VehicleRepositoryImpl(db)
        self.dozor_gps = DozorGpsAdapter()
        self.gps_guard = GpsGuardAdapter()
        self.mock_gps = MockGpsService()

    def _get_location(self, tracker_id: str, license_plate: Optional[str] = None):
        loc, updated = self.dozor_gps.get_vehicle_location(tracker_id, license_plate=license_plate)
        if loc:
            # #region agent log
            _debug_log_refresh("branch dozor", {"loc": loc[:80] if loc else None}, "A")
            # #endregion
            return loc, updated
        loc, updated = self.gps_guard.get_vehicle_location(tracker_id)
        if loc:
            # #region agent log
            _debug_log_refresh("branch guard", {"loc": loc[:80] if loc else None}, "A")
            # #endregion
            return loc, updated
        if self.dozor_gps.is_configured():
            # #region agent log
            _debug_log_refresh("branch none (dozor configured)", {"loc": None}, "A")
            # #endregion
            return None, None  # Dozor configured but no match — don't show Mock (Dortmund)
        loc, updated = self.mock_gps.get_vehicle_location(tracker_id)
        # #region agent log
        _debug_log_refresh("branch mock", {"loc": loc[:80] if loc else None}, "A")
        # #endregion
        return loc, updated

    def execute(self, vehicle_id: int) -> Optional[VehicleResponse]:
        vehicle = self.repository.get_by_id(vehicle_id)
        if not vehicle:
            return None
        # #region agent log
        _debug_log_refresh("execute", {"vehicle_id": vehicle_id, "gps_tracker_id": vehicle.gps_tracker_id if vehicle else None, "license_plate": vehicle.license_plate if vehicle else None}, "D")
        # #endregion
        if not vehicle.gps_tracker_id:
            return VehicleResponse.model_validate(vehicle)
        loc, last_updated = self._get_location(vehicle.gps_tracker_id, license_plate=vehicle.license_plate)
        vehicle.current_location = loc
        vehicle.gps_last_updated = last_updated
        updated = self.repository.save(vehicle)
        # #region agent log
        _debug_log_refresh("saved", {"final_loc": (loc[:80] if loc else None), "vehicle_id": vehicle_id}, "A")
        # #endregion
        return VehicleResponse.model_validate(updated)
