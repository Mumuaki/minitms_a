"""
Value Object: Route

Представляет маршрут перевозки с точками загрузки/выгрузки, расстоянием и временем.
"""

from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from backend.src.domain.value_objects.coordinates import Coordinates


@dataclass(frozen=True)
class RoutePoint:
    """
    Точка маршрута (загрузка или выгрузка).

    Attributes:
        coordinates: Координаты точки
        address: Адрес (город, страна и т.д.)
        operation: Тип операции ('loading' или 'unloading')
        planned_time: Планируемое время операции
    """
    coordinates: Coordinates
    address: str
    operation: str  # 'loading' or 'unloading'
    planned_time: Optional[datetime] = None

    def __post_init__(self):
        if self.operation not in ['loading', 'unloading']:
            raise ValueError("Operation must be 'loading' or 'unloading'")


@dataclass(frozen=True)
class Route:
    """
    Value Object для маршрута перевозки.

    Attributes:
        points: Список точек маршрута
        total_distance: Общее расстояние в км
        estimated_duration: Ожидаемая продолжительность
        fuel_consumption: Расход топлива в л/100км
        empty_run_distance: Расстояние порожнего пробега в км
    """
    points: List[RoutePoint]
    total_distance: float
    estimated_duration: timedelta
    fuel_consumption: Optional[float] = None
    empty_run_distance: Optional[float] = 0.0

    def __post_init__(self):
        if len(self.points) < 2:
            raise ValueError("Route must have at least 2 points")
        if self.total_distance < 0:
            raise ValueError("Total distance cannot be negative")
        if self.empty_run_distance is not None and self.empty_run_distance < 0:
            raise ValueError("Empty run distance cannot be negative")

    @property
    def loading_points(self) -> List[RoutePoint]:
        """Возвращает точки загрузки."""
        return [p for p in self.points if p.operation == 'loading']

    @property
    def unloading_points(self) -> List[RoutePoint]:
        """Возвращает точки выгрузки."""
        return [p for p in self.points if p.operation == 'unloading']

    @property
    def start_point(self) -> RoutePoint:
        """Первая точка маршрута."""
        return self.points[0]

    @property
    def end_point(self) -> RoutePoint:
        """Последняя точка маршрута."""
        return self.points[-1]

    def to_dict(self) -> dict:
        """Преобразует в словарь для JSON."""
        return {
            "points": [
                {
                    "coordinates": point.coordinates.to_dict(),
                    "address": point.address,
                    "operation": point.operation,
                    "planned_time": point.planned_time.isoformat() if point.planned_time else None
                }
                for point in self.points
            ],
            "total_distance": self.total_distance,
            "estimated_duration": self.estimated_duration.total_seconds(),
            "fuel_consumption": self.fuel_consumption,
            "empty_run_distance": self.empty_run_distance
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Route':
        """Создает объект из словаря."""
        points = [
            RoutePoint(
                coordinates=Coordinates.from_dict(p["coordinates"]),
                address=p["address"],
                operation=p["operation"],
                planned_time=datetime.fromisoformat(p["planned_time"]) if p.get("planned_time") else None
            )
            for p in data["points"]
        ]
        return cls(
            points=points,
            total_distance=data["total_distance"],
            estimated_duration=timedelta(seconds=data["estimated_duration"]),
            fuel_consumption=data.get("fuel_consumption"),
            empty_run_distance=data.get("empty_run_distance", 0.0)
        )