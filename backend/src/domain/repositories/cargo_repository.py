"""
Интерфейс репозитория грузов (Domain Layer).
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date

from backend.src.application.dto.cargo_dto import (
    SearchCargoRequestDto,
    SearchCargoResponseDto,
    CargoDto,
    CargoStatusColor
)


class CargoRepository(ABC):
    """Абстрактный класс репозитория грузов."""

    @abstractmethod
    def search_cargos(self, request: SearchCargoRequestDto) -> SearchCargoResponseDto:
        """Поиск грузов с фильтрами, сортировкой и пагинацией."""
        pass

    @abstractmethod
    def get_by_id(self, cargo_id: str) -> Optional[CargoDto]:
        """Получить груз по ID."""
        pass

    @abstractmethod
    def get_by_external_id(self, external_id: str) -> Optional[CargoDto]:
        """Получить груз по внешнему ID."""
        pass

    @abstractmethod
    def create(self, cargo: CargoDto) -> CargoDto:
        """Создать новый груз."""
        pass

    @abstractmethod
    def update(self, cargo: CargoDto) -> CargoDto:
        """Обновить груз."""
        pass

    @abstractmethod
    def delete(self, cargo_id: str) -> None:
        """Удалить груз."""
        pass