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

from backend.src.infrastructure.api.v1.dependencies import get_current_user, require_role
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
    
    orders = order_repo.get_all_for_period(period_start, period_end)
    total_fact_revenue = sum(o.revenue or 0.0 for o in orders)
    total_fact_margin = sum(o.margin or 0.0 for o in orders)
    total_fact_dist = sum(o.distance or 0.0 for o in orders)
    
    def get_color(fact, plan):
        if plan <= 0:
            return "green" if fact >= 0 else "red"
        shortfall = (plan - fact) / plan
        if shortfall <= 0.10:
            return "green"
        if shortfall <= 0.20:
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
    order_repo: OrderRepository = Depends(get_order_repository),
    current_user=Depends(get_current_user),
):
    """Детальный отчёт по рентабельности: список заказов и агрегация за период."""
    orders = order_repo.get_all_for_period(period_start, period_end)
    total_revenue = sum(o.revenue or 0.0 for o in orders)
    total_margin = sum(o.margin or 0.0 for o in orders)
    total_distance = sum(o.distance or 0.0 for o in orders)
    return {
        "period_start": str(period_start),
        "period_end": str(period_end),
        "orders_count": len(orders),
        "total_revenue": total_revenue,
        "total_margin": total_margin,
        "total_distance": total_distance,
        "avg_rate": (total_revenue / total_distance) if total_distance > 0 else 0.0,
        "orders": [
            {
                "id": o.id,
                "vehicle_id": o.vehicle_id,
                "revenue": o.revenue,
                "margin": o.margin,
                "distance": o.distance,
                "start_date": str(o.start_date),
                "end_date": str(o.end_date),
                "status": o.status.value if hasattr(o.status, "value") else o.status,
            }
            for o in orders
        ],
    }


@router.get("/export")
async def export_reports(
    format: str = "xlsx",
    current_user=Depends(require_role(['administrator','director','dispatcher'])),
):
    """Экспорт данных в Excel или PDF."""
    if format not in ["xlsx", "pdf"]:
        raise HTTPException(status_code=400, detail="Unsupported export format")
        
    # Заглушка
    return {"status": "ok", "message": f"Export functionality for {format} is pending integration."}
