"""
SQLAlchemy Implementation of PlanRepository
"""
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session

from backend.src.domain.entities.plan import FinancialPlan
from backend.src.domain.repositories.plan_repository import PlanRepository

class SqlAlchemyPlanRepository(PlanRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, plan_id: int) -> Optional[FinancialPlan]:
        return self.session.query(FinancialPlan).filter(FinancialPlan.id == plan_id).first()

    def get_by_vehicle_and_period(self, vehicle_id: int, start: date, end: date) -> Optional[FinancialPlan]:
        return self.session.query(FinancialPlan).filter(
            FinancialPlan.vehicle_id == vehicle_id,
            FinancialPlan.period_start == start,
            FinancialPlan.period_end == end
        ).first()

    def get_all_for_period(self, start: date, end: date) -> List[FinancialPlan]:
        return self.session.query(FinancialPlan).filter(
            FinancialPlan.period_start >= start,
            FinancialPlan.period_end <= end
        ).all()

    def save(self, plan: FinancialPlan) -> FinancialPlan:
        self.session.add(plan)
        self.session.commit()
        self.session.refresh(plan)
        return plan

    def delete(self, plan_id: int) -> bool:
        plan = self.get_by_id(plan_id)
        if plan:
            self.session.delete(plan)
            self.session.commit()
            return True
        return False
