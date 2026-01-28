"""
Use Case: SearchCargos

Бизнес-логика поиска грузов с фильтрами, сортировкой и пагинацией.
"""

from backend.src.domain.repositories.cargo_repository import CargoRepository
from backend.src.domain.services.profitability_calculator import ProfitabilityCalculator
from backend.src.application.dto.cargo_dto import (
    SearchCargoRequestDto,
    SearchCargoResponseDto,
    ProfitabilityDto
)


class SearchCargosUseCase:
    """
    Use Case для поиска грузов.

    Реализует поиск с расширенными фильтрами и сортировкой.
    """

    def __init__(self, cargo_repo: CargoRepository, profitability_calculator: ProfitabilityCalculator = None):
        """
        Args:
            cargo_repo: Репозиторий грузов.
            profitability_calculator: Калькулятор рентабельности.
        """
        self._cargo_repo = cargo_repo
        self._profitability_calculator = profitability_calculator or ProfitabilityCalculator()

    def execute(self, request: SearchCargoRequestDto) -> SearchCargoResponseDto:
        """
        Выполнить поиск грузов.

        Args:
            request: Параметры поиска с фильтрами, сортировкой и пагинацией.

        Returns:
            SearchCargoResponseDto с результатами поиска.
        """
        # Валидация параметров
        self._validate_request(request)

        # Выполнение поиска через репозиторий
        response = self._cargo_repo.search_cargos(request)

        # Расчет рентабельности для каждого груза
        if (request.fuel_consumption is not None or
            request.fuel_price is not None or
            request.depreciation_per_km is not None or
            request.driver_salary_per_km is not None or
            request.other_costs_per_km is not None):
            
            for cargo in response.items:
                distance = self._get_distance(cargo, request.distance_type)
                profitability_vo = self._profitability_calculator.calculate(
                    cargo_price=cargo.price,
                    distance=distance,
                    empty_run_distance=request.empty_run_distance,
                    fuel_consumption=request.fuel_consumption,
                    fuel_price=request.fuel_price,
                    depreciation_per_km=request.depreciation_per_km,
                    driver_salary_per_km=request.driver_salary_per_km,
                    other_costs_per_km=request.other_costs_per_km
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
        # Проверка диапазонов дат
        if (request.loading_date_from and request.loading_date_to and
            request.loading_date_from > request.loading_date_to):
            raise ValueError("loading_date_from cannot be after loading_date_to")

        if (request.unloading_date_from and request.unloading_date_to and
            request.unloading_date_from > request.unloading_date_to):
            raise ValueError("unloading_date_from cannot be after unloading_date_to")

        # Проверка диапазонов числовых значений
        if (request.weight_min is not None and request.weight_max is not None and
            request.weight_min > request.weight_max):
            raise ValueError("weight_min cannot be greater than weight_max")

        if (request.price_min is not None and request.price_max is not None and
            request.price_min > request.price_max):
            raise ValueError("price_min cannot be greater than price_max")

        if (request.distance_min is not None and request.distance_max is not None and
            request.distance_min > request.distance_max):
            raise ValueError("distance_min cannot be greater than distance_max")

        # Проверка типа расстояния
        if request.distance_type not in ["trans_eu", "osm"]:
            raise ValueError("distance_type must be 'trans_eu' or 'osm'")

        # Проверка направления сортировки
        if request.order_direction not in ["asc", "desc"]:
            raise ValueError("order_direction must be 'asc' or 'desc'")

        # Проверка поля сортировки (допустимые поля)
        allowed_order_fields = [
            "created_at", "price", "weight", "distance_trans_eu", "distance_osm",
            "rate_per_km", "total_cost", "loading_date", "unloading_date"
        ]
        if request.order_by not in allowed_order_fields:
            raise ValueError(f"order_by must be one of: {', '.join(allowed_order_fields)}")

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