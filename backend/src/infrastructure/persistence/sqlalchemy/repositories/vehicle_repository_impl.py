"""
SQLAlchemy реализация VehicleRepository.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.src.domain.repositories.vehicle_repository import VehicleRepository
# from backend.src.infrastructure.persistence.sqlalchemy.models.vehicle_model import Vehicle (Пока не реализовано)

class VehicleRepositoryImpl(VehicleRepository):
    """
    SQLAlchemy реализация репозитория ТС.
    """
    def __init__(self, session: Session):
        self._session = session

    def get_all(self) -> List[any]:
        # Заглушка, так как модель Vehicle еще не реализована
        return []

    def get_by_id(self, vehicle_id: str) -> Optional[any]:
        # Заглушка
        return None
