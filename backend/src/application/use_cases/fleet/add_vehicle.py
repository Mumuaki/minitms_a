from typing import Optional
from sqlalchemy.orm import Session
from backend.src.application.dto.vehicle_dto import VehicleCreate, VehicleResponse
from backend.src.domain.entities.vehicle import Vehicle, VehicleStatus
from backend.src.infrastructure.persistence.sqlalchemy.repositories.vehicle_repository_impl import VehicleRepositoryImpl

from backend.src.infrastructure.external_services.gps.mock_gps_service import MockGpsService
from backend.src.infrastructure.external_services.gps.gps_guard_adapter import GpsGuardAdapter
from backend.src.infrastructure.external_services.gps.dozor_gps_adapter import DozorGpsAdapter

class AddVehicleUseCase:
    def __init__(self, db: Session):
        self.repository = VehicleRepositoryImpl(db)
        self.dozor_gps = DozorGpsAdapter()
        self.gps_guard = GpsGuardAdapter()
        self.mock_gps = MockGpsService()

    def _get_location(self, tracker_id: str, license_plate: Optional[str] = None):
        # Prefer GPS Dozor; match by tracker_id (ODOKIRAGEN) or license_plate (BT152DH)
        loc, updated = self.dozor_gps.get_vehicle_location(tracker_id, license_plate=license_plate)
        if loc:
            return loc, updated
        loc, updated = self.gps_guard.get_vehicle_location(tracker_id)
        if loc:
            return loc, updated
        if self.dozor_gps.is_configured():
            return None, None  # Dozor configured but no match — don't show fake Mock location
        return self.mock_gps.get_vehicle_location(tracker_id)

    def execute(self, vehicle_data: VehicleCreate) -> VehicleResponse:
        vehicle = Vehicle(
            license_plate=vehicle_data.license_plate,
            vehicle_type=vehicle_data.vehicle_type,
            length=vehicle_data.length,
            width=vehicle_data.width,
            height=vehicle_data.height,
            payload_capacity=vehicle_data.payload_capacity,
            gps_tracker_id=vehicle_data.gps_tracker_id,
            status=VehicleStatus.FREE # Default status
        )
        
        # Fetch initial GPS data if tracker ID is provided
        if vehicle.gps_tracker_id:
            loc, last_updated = self._get_location(vehicle.gps_tracker_id, license_plate=vehicle.license_plate)
            vehicle.current_location = loc
            vehicle.gps_last_updated = last_updated
            
        saved_vehicle = self.repository.save(vehicle)
        return VehicleResponse.model_validate(saved_vehicle)
