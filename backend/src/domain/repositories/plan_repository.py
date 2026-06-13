"""
Domain Repository Interface: PlanRepository
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from backend.src.domain.entities.plan import FinancialPlan

class PlanRepository(ABC):
    @abstractmethod
    def get_by_id(self, plan_id: int) -> Optional[FinancialPlan]:
        pass

    @abstractmethod
    def get_by_vehicle_and_period(self, vehicle_id: int, start: date, end: date) -> Optional[FinancialPlan]:
        pass

    @abstractmethod
    def get_all_for_period(self, start: date, end: date) -> List[FinancialPlan]:
        pass

    @abstractmethod
    def save(self, plan: FinancialPlan) -> FinancialPlan:
        pass

    @abstractmethod
    def delete(self, plan_id: int) -> bool:
        pass
