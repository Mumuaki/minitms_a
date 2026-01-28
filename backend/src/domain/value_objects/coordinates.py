"""
Value Object: Coordinates

Представляет географические координаты (широта, долгота).
"""

from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class Coordinates:
    """
    Value Object для географических координат.

    Attributes:
        latitude: Широта (от -90 до 90)
        longitude: Долгота (от -180 до 180)
    """
    latitude: float
    longitude: float

    def __post_init__(self):
        if not (-90 <= self.latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= self.longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180")

    def to_dict(self) -> dict:
        """Преобразует в словарь для JSON."""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Coordinates':
        """Создает объект из словаря."""
        return cls(
            latitude=data["latitude"],
            longitude=data["longitude"]
        )