"""
Reports Endpoints.

Эндпоинты:
- GET /reports/dashboard-stats
- GET /reports/financial
- GET /reports/export
"""

from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.src.infrastructure.api.v1.dependencies import get_current_user
from backend.src.infrastructure.persistence.sqlalchemy.database import get_db
from backend.src.domain.repositories.order_repository import OrderRepository
from backend.src.domain.repositories.plan_repository import PlanRepository
from backend.src.infrastructure.persistence.sqlalchemy.repositories.order_repository import SqlAlchemyOrderRepository
from backend.src.infrastructure.persistence.sqlalchemy.repositories.plan_repository import SqlAlchemyPlanRepository

router = APIRouter(prefix="/reports", tags=["Reports"])

# ── Dependencies ──────────────────────────────────────────────────────────────

def get_order_repository(db: Session = Depends(get_db)) -> OrderRepository:
    return SqlAlchemyOrderRepository(db)

def get_plan_repository(db: Session = Depends(get_db)) -> PlanRepository:
    return SqlAlchemyPlanRepository(db)


# ── Schemas ───────────────────────────────────────────────────────────────────

class StatCard(BaseModel):
    plan: float
    fact: float
    unit: str
    status_color: str # "green", "yellow", "red"

class DashboardStatsResponse(BaseModel):
    revenue: StatCard
    margin: StatCard
    distance: StatCard
    avg_rate: float # fact_revenue / fact_distance


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/dashboard-stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    order_repo: OrderRepository = Depends(get_order_repository),
    plan_repo: PlanRepository = Depends(get_plan_repository),
    current_user=Depends(get_current_user),
):
    """
    Получение статистики "План / Факт" для дашборда (Агрегация из заказов и планов).
    """
    if not period_start:
        period_start = date(datetime.now().year, datetime.now().month, 1)
    if not period_end:
        period_end = date(datetime.now().year, 12, 31)
        
    plans = plan_repo.get_all_for_period(period_start, period_end)
    
    # В реальной реализации факт собирается со всех заказов за период
    # Здесь упрощенная агрегация для примера
    # TODO: Добавить метод `get_all_for_period` в OrderRepository без vehicle_id
    
    total_plan_revenue = sum(p.revenue_target for p in plans)
    total_plan_margin = sum(p.margin_target for p in plans)
    total_plan_dist = sum(p.distance_target for p in plans)
    
    # Заглушки для факта, пока не реализован сбор со всех авто (для примера)
    total_fact_revenue = 0.0
    total_fact_margin = 0.0
    total_fact_dist = 0.0
    
    def get_color(fact, plan):
        if plan == 0:
            return "green" if fact >= 0 else "red"
        deviation = (plan - fact) / plan
        if deviation <= 0:
            return "green"
        if deviation < 0.1:
            return "yellow"
        return "red"
        
    return DashboardStatsResponse(
        revenue=StatCard(
            plan=total_plan_revenue, 
            fact=total_fact_revenue, 
            unit="€", 
            status_color=get_color(total_fact_revenue, total_plan_revenue)
        ),
        margin=StatCard(
            plan=total_plan_margin, 
            fact=total_fact_margin, 
            unit="€", 
            status_color=get_color(total_fact_margin, total_plan_margin)
        ),
        distance=StatCard(
            plan=total_plan_dist, 
            fact=total_fact_dist, 
            unit="km", 
            status_color=get_color(total_fact_dist, total_plan_dist)
        ),
        avg_rate=total_fact_revenue / total_fact_dist if total_fact_dist > 0 else 0.0
    )


@router.get("/financial")
async def get_financial_report(
    period_start: date,
    period_end: date,
    current_user=Depends(get_current_user),
):
    """Детальный отчет по рентабельности. Возвращает список заказов и агрегацию."""
    # Заглушка до реализации
    return {"status": "ok", "message": "Detailed financial report will be implemented in future iterations."}


@router.get("/export")
async def export_reports(
    format: str = "xlsx",
    current_user=Depends(get_current_user),
):
    """Экспорт данных в Excel или PDF."""
    if format not in ["xlsx", "pdf"]:
        raise HTTPException(status_code=400, detail="Unsupported export format")
        
    # Заглушка
    return {"status": "ok", "message": f"Export functionality for {format} is pending integration."}
