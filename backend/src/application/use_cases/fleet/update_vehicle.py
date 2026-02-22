from sqlalchemy.orm import Session
from typing import Optional
from backend.src.application.dto.vehicle_dto import VehicleResponse, VehicleCreate
from backend.src.domain.entities.vehicle import Vehicle
from backend.src.infrastructure.persistence.sqlalchemy.repositories.vehicle_repository_impl import VehicleRepositoryImpl

from backend.src.infrastructure.external_services.gps.mock_gps_service import MockGpsService
from backend.src.infrastructure.external_services.gps.gps_guard_adapter import GpsGuardAdapter
from backend.src.infrastructure.external_services.gps.dozor_gps_adapter import DozorGpsAdapter

class UpdateVehicleUseCase:
    def __init__(self, db: Session):
        self.repository = VehicleRepositoryImpl(db)
        self.dozor_gps = DozorGpsAdapter()
        self.gps_guard = GpsGuardAdapter()
        self.mock_gps = MockGpsService()

    def _get_location(self, tracker_id: str):
        # Prefer GPS Dozor (same source as /gps/vehicles) so fleet shows real location
        loc, updated = self.dozor_gps.get_vehicle_location(tracker_id)
        if loc:
            return loc, updated
        loc, updated = self.gps_guard.get_vehicle_location(tracker_id)
        if loc:
            return loc, updated
        return self.mock_gps.get_vehicle_location(tracker_id)

    def execute(self, vehicle_id: int, vehicle_data: VehicleCreate) -> Optional[VehicleResponse]:
        vehicle = self.repository.get_by_id(vehicle_id)
        if not vehicle:
            return None
            
        # Check if tracker ID changed or just simple update
        tracker_changed = vehicle.gps_tracker_id != vehicle_data.gps_tracker_id
        
        # Update fields
        vehicle.license_plate = vehicle_data.license_plate
        vehicle.vehicle_type = vehicle_data.vehicle_type
        vehicle.length = vehicle_data.length
        vehicle.width = vehicle_data.width
        vehicle.height = vehicle_data.height
        vehicle.payload_capacity = vehicle_data.payload_capacity
        vehicle.gps_tracker_id = vehicle_data.gps_tracker_id
        
        # If tracker ID is present (new or existing) we might want to refresh location.
        # Logic: If changed OR valid and currently null location -> fetch.
        # For this task, let's always refresh if ID is present to simulate "pulling actual data".
        # If tracker ID is present (new or existing) we might want to refresh location.
        # Logic: If changed OR valid and currently null location -> fetch.
        # For this task, let's always refresh if ID is present to simulate "pulling actual data".
        if vehicle.gps_tracker_id:
             loc, last_updated = self._get_location(vehicle.gps_tracker_id)
             vehicle.current_location = loc
             vehicle.gps_last_updated = last_updated
        elif not vehicle.gps_tracker_id:
             # Cleared tracker - clear location
             vehicle.current_location = None
             vehicle.gps_last_updated = None
        
        updated_vehicle = self.repository.save(vehicle)
        return VehicleResponse.model_validate(updated_vehicle)
