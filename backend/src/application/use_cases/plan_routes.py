"""
Use Case: PlanRoutes

Use case для планирования маршрутов транспортных средств.
"""

from typing import List
from datetime import datetime

from backend.src.application.dto.route_planning_dto import (
    RoutePlanningRequest,
    RoutePlanningResponse,
    PlannedRouteDTO
)
from backend.src.domain.services.route_planner import RoutePlanner


class PlanRoutesUseCase:
    """
    Use case для планирования маршрутов.

    Координирует процесс планирования маршрутов на основе доступных грузов и ТС.
    """

    def __init__(self, route_planner: RoutePlanner):
        self.route_planner = route_planner

    def execute(self, request: RoutePlanningRequest) -> RoutePlanningResponse:
        """
        Выполняет планирование маршрутов.

        Args:
            request: Запрос на планирование

        Returns:
            RoutePlanningResponse: Результат планирования
        """
        # Выполняем планирование
        result = self.route_planner.plan_routes(
            available_cargo_ids=request.cargo_ids,
            available_vehicle_ids=request.vehicle_ids,
            planning_date=request.planning_date,
            max_routes_per_vehicle=request.max_routes_per_vehicle,
            max_cargos_per_route=request.max_cargos_per_route
        )

        # Преобразуем результат в DTO
        planned_routes_dto = []
        for planned_route in result.planned_routes:
            route_dto = PlannedRouteDTO(
                vehicle_id=planned_route.vehicle_id,
                route=planned_route.route.to_dict(),
                assigned_cargos=planned_route.assigned_cargos,
                total_profit=planned_route.total_profit,
                start_time=planned_route.start_time,
                end_time=planned_route.end_time
            )
            planned_routes_dto.append(route_dto)

        # Формируем сообщение
        message = self._generate_message(result)

        return RoutePlanningResponse(
            planned_routes=planned_routes_dto,
            unassigned_cargos=result.unassigned_cargos,
            total_profit=result.total_profit,
            message=message
        )

    def _generate_message(self, result) -> str:
        """
        Генерирует сообщение о результате планирования.
        """
        num_routes = len(result.planned_routes)
        num_assigned = sum(len(route.assigned_cargos) for route in result.planned_routes)
        num_unassigned = len(result.unassigned_cargos)

        message_parts = []

        if num_routes > 0:
            message_parts.append(f"Запланировано {num_routes} маршрутов")
            message_parts.append(f"Назначено {num_assigned} грузов")
        else:
            message_parts.append("Не удалось запланировать маршруты")

        if num_unassigned > 0:
            message_parts.append(f"Не назначено {num_unassigned} грузов")

        if result.total_profit > 0:
            message_parts.append(f"Ожидаемая прибыль: €{result.total_profit:.2f}")

        return ". ".join(message_parts)