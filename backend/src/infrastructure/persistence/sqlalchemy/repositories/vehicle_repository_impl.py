"""
SQLAlchemy реализация VehicleRepository.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.src.domain.repositories.vehicle_repository import VehicleRepository
from backend.src.domain.entities.vehicle import Vehicle

class VehicleRepositoryImpl(VehicleRepository):
    """
    SQLAlchemy реализация репозитория ТС.
    """
    def __init__(self, session: Session):
        self._session = session

    def get_all(self) -> List[Vehicle]:
        return self._session.query(Vehicle).all()

    def get_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        return self._session.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    def save(self, vehicle: Vehicle) -> Vehicle:
        self._session.add(vehicle)
        self._session.commit()
        self._session.refresh(vehicle)
        return vehicle

    def delete(self, vehicle_id: int) -> bool:
        vehicle = self._session.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if vehicle:
            self._session.delete(vehicle)
            self._session.commit()
            return True
        return False
