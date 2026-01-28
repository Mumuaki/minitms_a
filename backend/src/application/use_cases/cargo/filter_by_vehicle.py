"""
Use Case: FilterByVehicle

Бизнес-логика фильтрации грузов по характеристикам транспортного средства.
"""

from typing import List
from backend.src.domain.repositories.cargo_repository import CargoRepository
from backend.src.domain.services.profitability_calculator import ProfitabilityCalculator
from backend.src.application.dto.cargo_dto import (
    SearchCargoRequestDto,
    SearchCargoResponseDto,
    ProfitabilityDto
)


class FilterByVehicleUseCase:
    """
    Use Case для фильтрации грузов по транспортному средству.

    Реализует фильтрацию грузов на основе типа кузова, вместимости, веса,
    габаритов и других характеристик транспортного средства.
    """

    def __init__(self, cargo_repo: CargoRepository, profitability_calculator: ProfitabilityCalculator = None):
        """
        Args:
            cargo_repo: Репозиторий грузов.
            profitability_calculator: Калькулятор рентабельности.
        """
        self._cargo_repo = cargo_repo
        self._profitability_calculator = profitability_calculator or ProfitabilityCalculator()

    def execute(self, vehicle_body_type: str = None, vehicle_max_weight: float = None,
                vehicle_capacity: float = None, vehicle_length: float = None,
                vehicle_width: float = None, vehicle_height: float = None,
                fuel_consumption: float = None, fuel_price: float = None,
                depreciation_per_km: float = None, driver_salary_per_km: float = None,
                other_costs_per_km: float = None, empty_run_distance: float = 0,
                **search_params) -> SearchCargoResponseDto:
        """
        Выполнить фильтрацию грузов по ТС.

        Args:
            vehicle_body_type: Тип кузова ТС.
            vehicle_max_weight: Максимальный вес груза для ТС (т).
            vehicle_capacity: Вместимость ТС (м³).
            vehicle_length: Длина ТС (м).
            vehicle_width: Ширина ТС (м).
            vehicle_height: Высота ТС (м).
            fuel_consumption: Расход топлива (л/100км).
            fuel_price: Стоимость топлива (€/л).
            depreciation_per_km: Амортизация (€/км).
            driver_salary_per_km: Зарплата водителя (€/км).
            other_costs_per_km: Прочие расходы (€/км).
            empty_run_distance: Расстояние порожнего пробега (км).
            **search_params: Дополнительные параметры поиска (даты, цена и т.д.).

        Returns:
            SearchCargoResponseDto с отфильтрованными грузами.
        """
        # Создаем запрос с фильтрами по ТС
        request = SearchCargoRequestDto(
            vehicle_body_type=vehicle_body_type,
            vehicle_max_weight=vehicle_max_weight,
            vehicle_capacity=vehicle_capacity,
            vehicle_length=vehicle_length,
            vehicle_width=vehicle_width,
            vehicle_height=vehicle_height,
            fuel_consumption=fuel_consumption,
            fuel_price=fuel_price,
            depreciation_per_km=depreciation_per_km,
            driver_salary_per_km=driver_salary_per_km,
            other_costs_per_km=other_costs_per_km,
            empty_run_distance=empty_run_distance,
            **search_params
        )

        # Валидация параметров
        self._validate_request(request)

        # Выполнение поиска через репозиторий
        response = self._cargo_repo.search_cargos(request)

        # Расчет рентабельности для каждого груза
        if (fuel_consumption is not None or fuel_price is not None or
            depreciation_per_km is not None or driver_salary_per_km is not None or
            other_costs_per_km is not None):

            for cargo in response.items:
                distance = self._get_distance(cargo, request.distance_type)
                profitability_vo = self._profitability_calculator.calculate(
                    cargo_price=cargo.price,
                    distance=distance,
                    empty_run_distance=empty_run_distance,
                    fuel_consumption=fuel_consumption,
                    fuel_price=fuel_price,
                    depreciation_per_km=depreciation_per_km,
                    driver_salary_per_km=driver_salary_per_km,
                    other_costs_per_km=other_costs_per_km
                )
                cargo.profitability = ProfitabilityDto(
                    rate_per_km=profitability_vo.rate_per_km,
                    empty_run_km=profitability_vo.empty_run_km,
                    total_distance=profitability_vo.total_distance,
                    color_code=profitability_vo.status_color.value
                )

        return response

    def _get_distance(self, cargo, distance_type: str) -> float:
        """Получает расстояние из груза по указанному типу."""
        if distance_type == "trans_eu":
            return float(cargo.distance_trans_eu) if cargo.distance_trans_eu else 0
        else:
            return float(cargo.distance_osm) if cargo.distance_osm else 0

    def _validate_request(self, request: SearchCargoRequestDto) -> None:
        """
        Валидация параметров запроса.

        Args:
            request: Запрос для валидации.

        Raises:
            ValueError: Если параметры некорректны.
        """
        # Проверка параметров транспортного средства
        if request.vehicle_max_weight is not None and request.vehicle_max_weight < 0:
            raise ValueError("vehicle_max_weight cannot be negative")

        if request.vehicle_capacity is not None and request.vehicle_capacity < 0:
            raise ValueError("vehicle_capacity cannot be negative")

        if request.vehicle_length is not None and request.vehicle_length < 0:
            raise ValueError("vehicle_length cannot be negative")

        if request.vehicle_width is not None and request.vehicle_width < 0:
            raise ValueError("vehicle_width cannot be negative")

        if request.vehicle_height is not None and request.vehicle_height < 0:
            raise ValueError("vehicle_height cannot be negative")

        # Дополнительные проверки можно добавить по аналогии с SearchCargosUseCase