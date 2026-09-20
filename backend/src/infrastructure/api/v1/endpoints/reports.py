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


@router.get("/forecast")
async def get_forecast(
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    order_repo: OrderRepository = Depends(get_order_repository),
    plan_repo: PlanRepository = Depends(get_plan_repository),
    current_user=Depends(get_current_user),
):
    """Прогноз выполнения плана на конец периода (FR-PLAN-007) — линейная проекция факта."""
    import calendar
    if not period_start:
        now = datetime.now()
        period_start = date(now.year, now.month, 1)
    if not period_end:
        period_end = date(period_start.year, period_start.month, calendar.monthrange(period_start.year, period_start.month)[1])

    plans = plan_repo.get_all_for_period(period_start, period_end)
    orders = order_repo.get_all_for_period(period_start, period_end)
    plan_rev = sum(p.revenue_target for p in plans)
    plan_margin = sum(p.margin_target for p in plans)
    plan_dist = sum(p.distance_target for p in plans)
    fact_rev = sum(o.revenue or 0.0 for o in orders)
    fact_margin = sum(o.margin or 0.0 for o in orders)
    fact_dist = sum(o.distance or 0.0 for o in orders)

    today = date.today()
    total_days = (period_end - period_start).days + 1
    if today < period_start:
        elapsed = 0
    elif today > period_end:
        elapsed = total_days
    else:
        elapsed = (today - period_start).days + 1
    ratio = (total_days / elapsed) if elapsed > 0 else 1.0

    def pct(f, p):
        return round(f / p * 100, 1) if p else 0.0

    return {
        "period_start": str(period_start),
        "period_end": str(period_end),
        "elapsed_days": elapsed,
        "total_days": total_days,
        "plan": {"revenue": plan_rev, "margin": plan_margin, "distance": plan_dist},
        "fact": {"revenue": fact_rev, "margin": fact_margin, "distance": fact_dist},
        "forecast": {"revenue": round(fact_rev * ratio, 2), "margin": round(fact_margin * ratio, 2), "distance": round(fact_dist * ratio, 2)},
        "completion_pct": {"revenue": pct(fact_rev, plan_rev), "margin": pct(fact_margin, plan_margin), "distance": pct(fact_dist, plan_dist)},
    }


@router.get("/export")
async def export_reports(
    format: str = "csv",
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    order_repo: OrderRepository = Depends(get_order_repository),
    current_user=Depends(require_role(['administrator','director','dispatcher'])),
):
    """Экспорт отчёта по заказам (FR-REPORT-003): csv или xlsx."""
    if format not in ("csv", "xlsx", "pdf"):
        raise HTTPException(status_code=400, detail="Unsupported export format")
    if format == "pdf":
        raise HTTPException(status_code=501, detail="PDF export requires a PDF library (not installed)")

    if not period_start:
        period_start = date(datetime.now().year, 1, 1)
    if not period_end:
        period_end = date(datetime.now().year, 12, 31)
    orders = order_repo.get_all_for_period(period_start, period_end)

    from fastapi.responses import Response
    import io, csv

    rows = [["id", "vehicle_id", "start_date", "end_date", "revenue", "margin", "distance", "status"]]
    for o in orders:
        rows.append([
            o.id, o.vehicle_id, str(o.start_date), str(o.end_date),
            o.revenue, o.margin, o.distance,
            o.status.value if hasattr(o.status, "value") else o.status,
        ])

    if format == "csv":
        buf = io.StringIO()
        csv.writer(buf).writerows(rows)
        return Response(content=buf.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=report.csv"})

    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Report"
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=report.xlsx"},
    )
