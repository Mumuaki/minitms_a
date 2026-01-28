"""
Domain Service: RoutePlanner

Сервис для планирования маршрутов транспортных средств на основе доступных грузов.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from backend.src.domain.value_objects.route import Route, RoutePoint
from backend.src.domain.value_objects.coordinates import Coordinates
from backend.src.domain.services.route_optimizer import RouteOptimizer
from backend.src.domain.services.profitability_calculator import ProfitabilityCalculator
from backend.src.domain.repositories.cargo_repository import CargoRepository
from backend.src.domain.repositories.vehicle_repository import VehicleRepository


@dataclass
class PlannedRoute:
    """
    Планируемый маршрут для транспортного средства.

    Attributes:
        vehicle_id: ID транспортного средства
        route: Маршрут
        assigned_cargos: Список ID назначенных грузов
        total_profit: Общая прибыль
        start_time: Время начала маршрута
        end_time: Время окончания маршрута
    """
    vehicle_id: str
    route: Route
    assigned_cargos: List[str]
    total_profit: float
    start_time: datetime
    end_time: datetime


@dataclass
class RoutePlanningResult:
    """
    Результат планирования маршрутов.

    Attributes:
        planned_routes: Список планируемых маршрутов
        unassigned_cargos: Список ID грузов, которые не удалось назначить
        total_profit: Общая прибыль от всех маршрутов
    """
    planned_routes: List[PlannedRoute]
    unassigned_cargos: List[str]
    total_profit: float


class RoutePlanner:
    """
    Сервис для планирования маршрутов транспортных средств.

    Анализирует доступные грузы и транспортные средства, оптимизирует маршруты
    для максимальной прибыли и эффективности.
    """

    def __init__(
        self,
        route_optimizer: RouteOptimizer,
        profitability_calculator: ProfitabilityCalculator,
        cargo_repository: CargoRepository,
        vehicle_repository: VehicleRepository
    ):
        self.route_optimizer = route_optimizer
        self.profitability_calculator = profitability_calculator
        self.cargo_repository = cargo_repository
        self.vehicle_repository = vehicle_repository

    def plan_routes(
        self,
        available_cargo_ids: List[str],
        available_vehicle_ids: List[str],
        planning_date: datetime,
        max_routes_per_vehicle: int = 1,
        max_cargos_per_route: int = 3
    ) -> RoutePlanningResult:
        """
        Планирует маршруты для транспортных средств на основе доступных грузов.

        Args:
            available_cargo_ids: Список ID доступных грузов
            available_vehicle_ids: Список ID доступных транспортных средств
            planning_date: Дата планирования
            max_routes_per_vehicle: Максимальное количество маршрутов на ТС
            max_cargos_per_route: Максимальное количество грузов на маршрут

        Returns:
            RoutePlanningResult: Результат планирования
        """
        # Получаем данные о грузах и ТС
        cargos = self.cargo_repository.get_by_ids(available_cargo_ids)
        vehicles = self.vehicle_repository.get_by_ids(available_vehicle_ids)

        # Фильтруем грузы по совместимости с ТС
        compatible_assignments = self._find_compatible_assignments(cargos, vehicles)

        # Оптимизируем назначения для максимальной прибыли
        planned_routes, unassigned_cargos = self._optimize_assignments(
            compatible_assignments,
            planning_date,
            max_routes_per_vehicle,
            max_cargos_per_route
        )

        total_profit = sum(route.total_profit for route in planned_routes)

        return RoutePlanningResult(
            planned_routes=planned_routes,
            unassigned_cargos=unassigned_cargos,
            total_profit=total_profit
        )

    def _find_compatible_assignments(
        self,
        cargos: List,
        vehicles: List
    ) -> Dict[str, List[str]]:
        """
        Находит совместимые назначения грузов транспортным средствам.

        Returns:
            Dict[vehicle_id, List[cargo_ids]]: Совместимые назначения
        """
        assignments = {}

        for vehicle in vehicles:
            compatible_cargos = []

            for cargo in cargos:
                if self._is_cargo_compatible_with_vehicle(cargo, vehicle):
                    compatible_cargos.append(cargo.id)

            assignments[vehicle.id] = compatible_cargos

        return assignments

    def _is_cargo_compatible_with_vehicle(self, cargo, vehicle) -> bool:
        """
        Проверяет совместимость груза с транспортным средством.

        Проверяет вес, тип кузова, даты и т.д.
        """
        # Проверка веса
        if cargo.weight and vehicle.max_weight and cargo.weight > vehicle.max_weight:
            return False

        # Проверка типа кузова
        if cargo.body_type and vehicle.body_type and cargo.body_type != vehicle.body_type:
            return False

        # Проверка дат (упрощенная)
        if cargo.loading_date and cargo.unloading_date:
            # ТС должно быть доступно в эти даты
            pass

        return True

    def _optimize_assignments(
        self,
        compatible_assignments: Dict[str, List[str]],
        planning_date: datetime,
        max_routes_per_vehicle: int,
        max_cargos_per_route: int
    ) -> Tuple[List[PlannedRoute], List[str]]:
        """
        Оптимизирует назначения для максимальной прибыли.

        Использует жадный алгоритм для простоты.
        """
        planned_routes = []
        assigned_cargos = set()
        unassigned_cargos = []

        # Получаем все грузы
        all_cargo_ids = set()
        for cargo_ids in compatible_assignments.values():
            all_cargo_ids.update(cargo_ids)

        # Сортируем грузы по рентабельности (от большего к меньшему)
        cargo_profitability = {}
        for cargo_id in all_cargo_ids:
            cargo = self.cargo_repository.get_by_id(cargo_id)
            if cargo and cargo.price and cargo.distance_osm:
                profitability = self.profitability_calculator.calculate(
                    cargo_price=cargo.price,
                    distance=cargo.distance_osm
                )
                cargo_profitability[cargo_id] = profitability.rate_per_km or 0
            else:
                cargo_profitability[cargo_id] = 0

        sorted_cargos = sorted(
            all_cargo_ids,
            key=lambda x: cargo_profitability.get(x, 0),
            reverse=True
        )

        # Назначаем грузы транспортным средствам
        for vehicle_id, compatible_cargo_ids in compatible_assignments.items():
            vehicle_assigned_cargos = []

            for cargo_id in sorted_cargos:
                if cargo_id in compatible_cargo_ids and cargo_id not in assigned_cargos:
                    vehicle_assigned_cargos.append(cargo_id)
                    assigned_cargos.add(cargo_id)

                    if len(vehicle_assigned_cargos) >= max_cargos_per_route:
                        break

            if vehicle_assigned_cargos:
                # Создаем маршрут для назначенных грузов
                route = self._create_route_for_cargos(vehicle_assigned_cargos, planning_date)
                if route:
                    # Рассчитываем прибыль
                    total_profit = self._calculate_route_profit(route, vehicle_assigned_cargos)

                    planned_route = PlannedRoute(
                        vehicle_id=vehicle_id,
                        route=route,
                        assigned_cargos=vehicle_assigned_cargos,
                        total_profit=total_profit,
                        start_time=planning_date,
                        end_time=planning_date + route.estimated_duration
                    )
                    planned_routes.append(planned_route)

        # Не назначенные грузы
        unassigned_cargos = list(all_cargo_ids - assigned_cargos)

        return planned_routes, unassigned_cargos

    def _create_route_for_cargos(self, cargo_ids: List[str], start_date: datetime) -> Optional[Route]:
        """
        Создает маршрут для списка грузов.
        """
        if not cargo_ids:
            return None

        points = []

        for cargo_id in cargo_ids:
            cargo = self.cargo_repository.get_by_id(cargo_id)
            if not cargo:
                continue

            # Точка загрузки
            loading_coords = Coordinates(
                latitude=cargo.loading_place.get('coordinates', {}).get('latitude', 0),
                longitude=cargo.loading_place.get('coordinates', {}).get('longitude', 0)
            )
            loading_address = cargo.loading_place.get('city', '') + ', ' + cargo.loading_place.get('country', '')

            points.append(RoutePoint(
                coordinates=loading_coords,
                address=loading_address,
                operation='loading',
                planned_time=cargo.loading_date and datetime.combine(cargo.loading_date, datetime.min.time()) or None
            ))

            # Точка выгрузки
            unloading_coords = Coordinates(
                latitude=cargo.unloading_place.get('coordinates', {}).get('latitude', 0),
                longitude=cargo.unloading_place.get('coordinates', {}).get('longitude', 0)
            )
            unloading_address = cargo.unloading_place.get('city', '') + ', ' + cargo.unloading_place.get('country', '')

            points.append(RoutePoint(
                coordinates=unloading_coords,
                address=unloading_address,
                operation='unloading',
                planned_time=cargo.unloading_date and datetime.combine(cargo.unloading_date, datetime.min.time()) or None
            ))

        if len(points) < 2:
            return None

        # Оптимизируем маршрут
        return self.route_optimizer.optimize_route(points)

    def _calculate_route_profit(self, route: Route, cargo_ids: List[str]) -> float:
        """
        Рассчитывает общую прибыль от маршрута.
        """
        total_profit = 0.0

        for cargo_id in cargo_ids:
            cargo = self.cargo_repository.get_by_id(cargo_id)
            if cargo and cargo.price:
                profitability = self.profitability_calculator.calculate(
                    cargo_price=cargo.price,
                    distance=route.total_distance,
                    empty_run_distance=route.empty_run_distance
                )
                if profitability.rate_per_km:
                    total_profit += profitability.rate_per_km * route.total_distance

        return total_profit