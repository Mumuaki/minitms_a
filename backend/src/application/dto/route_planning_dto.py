"""
DTO: RoutePlanning

DTO для запросов и ответов планирования маршрутов.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from backend.src.domain.value_objects.route import Route


class RoutePlanningRequest(BaseModel):
    """
    Запрос на планирование маршрутов.

    Attributes:
        cargo_ids: Список ID грузов для планирования
        vehicle_ids: Список ID доступных транспортных средств
        planning_date: Дата планирования
        max_routes_per_vehicle: Максимальное количество маршрутов на ТС
        max_cargos_per_route: Максимальное количество грузов на маршрут
    """
    cargo_ids: List[str] = Field(..., description="Список ID грузов")
    vehicle_ids: List[str] = Field(..., description="Список ID транспортных средств")
    planning_date: datetime = Field(..., description="Дата планирования")
    max_routes_per_vehicle: Optional[int] = Field(1, description="Макс маршрутов на ТС")
    max_cargos_per_route: Optional[int] = Field(3, description="Макс грузов на маршрут")


class PlannedRouteDTO(BaseModel):
    """
    DTO для планируемого маршрута.

    Attributes:
        vehicle_id: ID транспортного средства
        route: Маршрут
        assigned_cargos: Назначенные грузы
        total_profit: Общая прибыль
        start_time: Время начала
        end_time: Время окончания
    """
    vehicle_id: str
    route: dict  # Route.to_dict()
    assigned_cargos: List[str]
    total_profit: float
    start_time: datetime
    end_time: datetime


class RoutePlanningResponse(BaseModel):
    """
    Ответ на запрос планирования маршрутов.

    Attributes:
        planned_routes: Список планируемых маршрутов
        unassigned_cargos: Не назначенные грузы
        total_profit: Общая прибыль
        message: Сообщение о результате
    """
    planned_routes: List[PlannedRouteDTO]
    unassigned_cargos: List[str]
    total_profit: float
    message: str = Field("", description="Сообщение о результате")