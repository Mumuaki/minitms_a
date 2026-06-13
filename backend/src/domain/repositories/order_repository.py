"""
Domain Repository Interface: OrderRepository
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from backend.src.domain.entities.order import Order

class OrderRepository(ABC):
    @abstractmethod
    def get_by_id(self, order_id: int) -> Optional[Order]:
        pass

    @abstractmethod
    def get_all_for_vehicle(self, vehicle_id: int, start: date, end: date) -> List[Order]:
        pass

    @abstractmethod
    def save(self, order: Order) -> Order:
        pass
