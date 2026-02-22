"""
Financial Planning Endpoints.

Эндпоинты:
- GET  /financial/plans     — список финансовых планов
- POST /financial/plans     — создать план
- GET  /financial/dashboard — сводная статистика
"""

from typing import List, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from backend.src.infrastructure.api.v1.dependencies import get_current_user

router = APIRouter(prefix="/financial", tags=["Financial Planning"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class FinancialPlan(BaseModel):
    id: int
    name: str
    period_start: str
    period_end: str
    revenue_target: float
    revenue_actual: float
    expenses_target: float
    expenses_actual: float
    profit_target: float
    profit_actual: float
    currency: str
    status: str
    created_at: str


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


# ── Sample data ───────────────────────────────────────────────────────────────

_PLANS: List[FinancialPlan] = [
    FinancialPlan(
        id=1,
        name="Q1 2026",
        period_start="2026-01-01",
        period_end="2026-03-31",
        revenue_target=150000.0,
        revenue_actual=142500.0,
        expenses_target=110000.0,
        expenses_actual=108200.0,
        profit_target=40000.0,
        profit_actual=34300.0,
        currency="EUR",
        status="active",
        created_at="2026-01-01T00:00:00",
    ),
    FinancialPlan(
        id=2,
        name="Q2 2026",
        period_start="2026-04-01",
        period_end="2026-06-30",
        revenue_target=180000.0,
        revenue_actual=0.0,
        expenses_target=125000.0,
        expenses_actual=0.0,
        profit_target=55000.0,
        profit_actual=0.0,
        currency="EUR",
        status="planned",
        created_at="2026-01-15T00:00:00",
    ),
]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/plans", response_model=List[FinancialPlan])
async def get_financial_plans(
    status_filter: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """Список финансовых планов."""
    plans = _PLANS
    if status_filter:
        plans = [p for p in plans if p.status == status_filter]
    return plans


@router.post("/plans", response_model=FinancialPlan, status_code=status.HTTP_201_CREATED)
async def create_financial_plan(
    name: str,
    period_start: str,
    period_end: str,
    revenue_target: float,
    expenses_target: float,
    currency: str = "EUR",
    current_user=Depends(get_current_user),
):
    """Создать новый финансовый план."""
    new_id = max(p.id for p in _PLANS) + 1 if _PLANS else 1
    plan = FinancialPlan(
        id=new_id,
        name=name,
        period_start=period_start,
        period_end=period_end,
        revenue_target=revenue_target,
        revenue_actual=0.0,
        expenses_target=expenses_target,
        expenses_actual=0.0,
        profit_target=revenue_target - expenses_target,
        profit_actual=0.0,
        currency=currency,
        status="planned",
        created_at=datetime.utcnow().isoformat(),
    )
    _PLANS.append(plan)
    return plan


@router.get("/dashboard", response_model=FinancialDashboard)
async def get_financial_dashboard(
    current_user=Depends(get_current_user),
):
    """Сводная финансовая статистика за текущий месяц."""
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
