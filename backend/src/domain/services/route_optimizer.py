"""
Domain Service: RouteOptimizer

Сервис для оптимизации маршрутов. Рассчитывает расстояния, время и оптимизирует порядок точек.
"""

from typing import List, Optional
from datetime import timedelta

from backend.src.domain.value_objects.route import Route, RoutePoint
from backend.src.domain.value_objects.coordinates import Coordinates
from backend.src.application.ports.maps_port import MapsPort


class RouteOptimizer:
    """
    Сервис для оптимизации маршрутов.

    Использует внешние сервисы карт для расчета расстояний и времени.
    """

    def __init__(self, maps_service: MapsPort):
        self.maps_service = maps_service

    def optimize_route(
        self,
        points: List[RoutePoint],
        vehicle_type: Optional[str] = None
    ) -> Route:
        """
        Оптимизирует маршрут, рассчитывая расстояние и время.

        Args:
            points: Список точек маршрута
            vehicle_type: Тип транспортного средства (для учета ограничений)

        Returns:
            Route: Оптимизированный маршрут
        """
        if len(points) < 2:
            raise ValueError("Route must have at least 2 points")

        # Для простоты предполагаем, что точки уже в оптимальном порядке
        # В реальной реализации здесь был бы алгоритм оптимизации (TSP и т.д.)

        # Рассчитываем общее расстояние и время
        total_distance = 0.0
        total_duration = timedelta()

        for i in range(len(points) - 1):
            start = points[i].coordinates
            end = points[i + 1].coordinates

            # Используем внешний сервис для расчета расстояния
            distance, duration = self.maps_service.calculate_distance_and_time(
                start, end, vehicle_type
            )

            total_distance += distance
            total_duration += duration

        # Предполагаем расход топлива (можно параметризовать)
        fuel_consumption = 25.0  # л/100км по умолчанию

        return Route(
            points=points,
            total_distance=total_distance,
            estimated_duration=total_duration,
            fuel_consumption=fuel_consumption
        )

    def calculate_distance(
        self,
        start: Coordinates,
        end: Coordinates,
        vehicle_type: Optional[str] = None
    ) -> float:
        """
        Рассчитывает расстояние между двумя точками.

        Args:
            start: Начальная точка
            end: Конечная точка
            vehicle_type: Тип транспортного средства

        Returns:
            float: Расстояние в км
        """
        distance, _ = self.maps_service.calculate_distance_and_time(start, end, vehicle_type)
        return distance

    def calculate_travel_time(
        self,
        start: Coordinates,
        end: Coordinates,
        vehicle_type: Optional[str] = None
    ) -> timedelta:
        """
        Рассчитывает время в пути между двумя точками.

        Args:
            start: Начальная точка
            end: Конечная точка
            vehicle_type: Тип транспортного средства

        Returns:
            timedelta: Время в пути
        """
        _, duration = self.maps_service.calculate_distance_and_time(start, end, vehicle_type)
        return duration