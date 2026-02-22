from typing import List
from sqlalchemy.orm import Session
from backend.src.application.dto.vehicle_dto import VehicleResponse
from backend.src.infrastructure.persistence.sqlalchemy.repositories.vehicle_repository_impl import VehicleRepositoryImpl

class GetAllVehiclesUseCase:
    def __init__(self, db: Session):
        self.repository = VehicleRepositoryImpl(db)

    def execute(self) -> List[VehicleResponse]:
        vehicles = self.repository.get_all()
        return [VehicleResponse.model_validate(vehicle) for vehicle in vehicles]
