"""
Financial Planning Endpoints.

Эндпоинты:
- GET  /financial/plans     — список финансовых планов
- POST /financial/plans     — создать план
- GET  /financial/dashboard — сводная статистика
"""

from typing import List, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.src.infrastructure.api.v1.dependencies import get_current_user, require_role
from backend.src.infrastructure.persistence.sqlalchemy.database import get_db
from backend.src.domain.repositories.plan_repository import PlanRepository
from backend.src.infrastructure.persistence.sqlalchemy.repositories.plan_repository import SqlAlchemyPlanRepository
from backend.src.domain.entities.plan import FinancialPlan as FinancialPlanEntity

router = APIRouter(prefix="/financial", tags=["Financial Planning"])

# ── Dependencies ──────────────────────────────────────────────────────────────

def get_plan_repository(db: Session = Depends(get_db)) -> PlanRepository:
    return SqlAlchemyPlanRepository(db)

# ── Schemas ───────────────────────────────────────────────────────────────────

class FinancialPlanResponse(BaseModel):
    id: int
    vehicle_id: int
    period_start: date
    period_end: date
    revenue_target: float
    margin_target: float
    distance_target: float
    currency: str
    
    class Config:
        from_attributes = True

class FinancialPlanCreate(BaseModel):
    vehicle_id: int
    period_start: date
    period_end: date
    revenue_target: float
    margin_target: float
    distance_target: float
    currency: str = "EUR"

class FinancialDashboard(BaseModel):
    period: str
    total_revenue: float
    total_expenses: float
    net_profit: float
    profit_margin: float
    trips_completed: int
    avg_revenue_per_trip: float
    fuel_costs: float
    maintenance_costs: float
    salary_costs: float
    revenue_trend: List[dict]
    top_routes: List[dict]
    currency: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/plans", response_model=List[FinancialPlanResponse])
async def get_financial_plans(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    repo: PlanRepository = Depends(get_plan_repository),
    current_user=Depends(get_current_user),
):
    """Список финансовых планов."""
    if not start_date:
        start_date = date(datetime.now().year, datetime.now().month, 1)
    if not end_date:
        end_date = date(datetime.now().year, 12, 31)
        
    plans = repo.get_all_for_period(start_date, end_date)
    return plans


@router.post("/plans", response_model=FinancialPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_financial_plan(
    plan_in: FinancialPlanCreate,
    repo: PlanRepository = Depends(get_plan_repository),
    current_user=Depends(require_role(['administrator','director'])),
):
    """Создать новый финансовый план."""
    existing = repo.get_by_vehicle_and_period(plan_in.vehicle_id, plan_in.period_start, plan_in.period_end)
    if existing:
        raise HTTPException(status_code=400, detail="Plan already exists for this vehicle in this period")
        
    new_plan = FinancialPlanEntity(
        vehicle_id=plan_in.vehicle_id,
        period_start=plan_in.period_start,
        period_end=plan_in.period_end,
        revenue_target=plan_in.revenue_target,
        margin_target=plan_in.margin_target,
        distance_target=plan_in.distance_target,
        currency=plan_in.currency
    )
    saved_plan = repo.save(new_plan)
    return saved_plan


@router.get("/dashboard", response_model=FinancialDashboard)
async def get_financial_dashboard(
    current_user=Depends(get_current_user),
):
    """
    Сводная финансовая статистика. 
    В реальной системе здесь будет агрегация данных из OrderRepository и PlanRepository.
    Пока возвращаем мок для сохранения структуры дашборда до реализации Fact Stats.
    """
    return FinancialDashboard(
        period="February 2026",
        total_revenue=48500.0,
        total_expenses=36200.0,
        net_profit=12300.0,
        profit_margin=25.36,
        trips_completed=34,
        avg_revenue_per_trip=1426.47,
        fuel_costs=14200.0,
        maintenance_costs=3800.0,
        salary_costs=12000.0,
        revenue_trend=[
            {"month": "Sep 2025", "revenue": 38200, "expenses": 29100},
            {"month": "Oct 2025", "revenue": 41500, "expenses": 31800},
            {"month": "Nov 2025", "revenue": 39800, "expenses": 30200},
            {"month": "Dec 2025", "revenue": 44100, "expenses": 33600},
            {"month": "Jan 2026", "revenue": 46300, "expenses": 35100},
            {"month": "Feb 2026", "revenue": 48500, "expenses": 36200},
        ],
        top_routes=[
            {"route": "Київ → Варшава", "trips": 8, "revenue": 12400.0},
            {"route": "Львів → Берлін", "trips": 6, "revenue": 10200.0},
            {"route": "Одеса → Бухарест", "trips": 5, "revenue": 7800.0},
        ],
        currency="EUR",
    )
