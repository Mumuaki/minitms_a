"""Refresh vehicle current_location from GPS (Dozor first, then Guard, then mock)."""
from typing import Optional
from sqlalchemy.orm import Session

from backend.src.application.dto.vehicle_dto import VehicleResponse
from backend.src.infrastructure.persistence.sqlalchemy.repositories.vehicle_repository_impl import VehicleRepositoryImpl
from backend.src.infrastructure.external_services.gps.dozor_gps_adapter import DozorGpsAdapter
from backend.src.infrastructure.external_services.gps.gps_guard_adapter import GpsGuardAdapter
from backend.src.infrastructure.external_services.gps.mock_gps_service import MockGpsService


class RefreshVehicleLocationUseCase:
    def __init__(self, db: Session):
        self.repository = VehicleRepositoryImpl(db)
        self.dozor_gps = DozorGpsAdapter()
        self.gps_guard = GpsGuardAdapter()
        self.mock_gps = MockGpsService()

    def _get_location(self, tracker_id: str):
        loc, updated = self.dozor_gps.get_vehicle_location(tracker_id)
        if loc:
            return loc, updated
        loc, updated = self.gps_guard.get_vehicle_location(tracker_id)
        if loc:
            return loc, updated
        return self.mock_gps.get_vehicle_location(tracker_id)

    def execute(self, vehicle_id: int) -> Optional[VehicleResponse]:
        vehicle = self.repository.get_by_id(vehicle_id)
        if not vehicle:
            return None
        if not vehicle.gps_tracker_id:
            return VehicleResponse.model_validate(vehicle)
        loc, last_updated = self._get_location(vehicle.gps_tracker_id)
        vehicle.current_location = loc
        vehicle.gps_last_updated = last_updated
        updated = self.repository.save(vehicle)
        return VehicleResponse.model_validate(updated)
