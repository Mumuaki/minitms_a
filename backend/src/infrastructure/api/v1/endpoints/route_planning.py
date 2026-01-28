"""
API Endpoint: Route Planning

Эндпоинт для планирования маршрутов транспортных средств.
"""

from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from backend.src.application.dto.route_planning_dto import (
    RoutePlanningRequest,
    RoutePlanningResponse
)
from backend.src.application.use_cases.plan_routes import PlanRoutesUseCase
from backend.src.infrastructure.api.v1.dependencies import (
    get_plan_routes_use_case,
    require_role
)

router = APIRouter(prefix="/route-planning", tags=["Route Planning"])


@router.post("/", response_model=RoutePlanningResponse)
async def plan_routes(
    request: RoutePlanningRequest,
    use_case: PlanRoutesUseCase = Depends(get_plan_routes_use_case),
    _: None = Depends(require_role(["admin", "dispatcher"]))
) -> RoutePlanningResponse:
    """
    Планирует маршруты для транспортных средств на основе доступных грузов.

    Требуемые роли: admin, dispatcher

    Args:
        request: Параметры планирования маршрутов

    Returns:
        RoutePlanningResponse: Результат планирования
    """
    try:
        result = use_case.execute(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при планировании маршрутов: {str(e)}"
        )


@router.post("/optimize", response_model=RoutePlanningResponse)
async def optimize_routes(
    cargo_ids: List[str],
    vehicle_ids: List[str],
    planning_date: datetime,
    use_case: PlanRoutesUseCase = Depends(get_plan_routes_use_case),
    _: None = Depends(require_role(["admin", "dispatcher"]))
) -> RoutePlanningResponse:
    """
    Оптимизирует маршруты с параметрами по умолчанию.

    Требуемые роли: admin, dispatcher

    Args:
        cargo_ids: Список ID грузов
        vehicle_ids: Список ID транспортных средств
        planning_date: Дата планирования

    Returns:
        RoutePlanningResponse: Результат планирования
    """
    request = RoutePlanningRequest(
        cargo_ids=cargo_ids,
        vehicle_ids=vehicle_ids,
        planning_date=planning_date
    )

    try:
        result = use_case.execute(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при оптимизации маршрутов: {str(e)}"
        )