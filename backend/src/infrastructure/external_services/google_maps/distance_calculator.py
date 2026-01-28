"""
Реализация калькулятора дистанций через Google Maps (или аналог).
"""
from typing import Optional, Tuple
from backend.src.application.ports.maps_port import MapsPort

class GoogleMapsDistanceCalculator(MapsPort):
    """
    Реализация MapsPort.
    """
    
    def calculate_distance(self, origin: str, destination: str) -> float:
        # TODO: Реализовать запрос к Google Maps API или OSM
        return 0.0

    def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        # TODO: Реализовать геокодинг
        return None
