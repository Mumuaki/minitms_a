"""
Интерфейс репозитория транспортных средств (Domain Layer).
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from backend.src.domain.entities.vehicle import Vehicle

class VehicleRepository(ABC):
    """Абстрактный класс репозитория ТС."""
    
    @abstractmethod
    def get_all(self) -> List[Vehicle]:
        """Получить список всех ТС."""
        pass

    @abstractmethod
    def get_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        """Получить ТС по ID."""
        pass
        
    @abstractmethod
    def save(self, vehicle: Vehicle) -> Vehicle:
        """Сохранить или обновить ТС."""
        pass

    @abstractmethod
    def delete(self, vehicle_id: int) -> bool:
        """Удалить ТС по ID."""
        pass
