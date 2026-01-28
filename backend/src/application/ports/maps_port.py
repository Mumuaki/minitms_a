"""
Интерфейс порта для работы с картами (расчет расстояний, геокодинг).
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple

class MapsPort(ABC):
    """
    Интерфейс для внешних картографических сервисов (Google Maps, OSM).
    """
    
    @abstractmethod
    def calculate_distance(self, origin: str, destination: str) -> float:
        """
        Рассчитывает расстояние между двумя точками в км.
        """
        pass

    @abstractmethod
    def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Получает координаты (lat, lon) по адресу.
        """
        pass
