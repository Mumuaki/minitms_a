from sqlalchemy.orm import Session
from backend.src.infrastructure.persistence.sqlalchemy.repositories.vehicle_repository_impl import VehicleRepositoryImpl

class DeleteVehicleUseCase:
    def __init__(self, db: Session):
        self.repository = VehicleRepositoryImpl(db)

    def execute(self, vehicle_id: int) -> bool:
        return self.repository.delete(vehicle_id)
