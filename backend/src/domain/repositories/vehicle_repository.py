"""
Интерфейс репозитория транспортных средств (Domain Layer).
"""
from abc import ABC, abstractmethod
from typing import List, Optional
# Так как сущность Vehicle пустая, используем Any или создадим заглушку позже, 
# но для успешного импорта пока сделаем так:
# from backend.src.domain.entities.vehicle import Vehicle (Vehicle пустой)

class VehicleRepository(ABC):
    """Абстрактный класс репозитория ТС."""
    
    @abstractmethod
    def get_all(self) -> List[any]:
        pass

    @abstractmethod
    def get_by_id(self, vehicle_id: str) -> Optional[any]:
        pass
