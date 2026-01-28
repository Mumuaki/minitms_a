"""
Unit Tests: RoutePlanner

Тесты для сервиса планирования маршрутов.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from backend.src.domain.services.route_planner import RoutePlanner, PlannedRoute, RoutePlanningResult
from backend.src.domain.value_objects.route import Route, RoutePoint
from backend.src.domain.value_objects.coordinates import Coordinates


class TestRoutePlanner:
    """Тесты для RoutePlanner."""

    @pytest.fixture
    def mock_route_optimizer(self):
        """Мок для RouteOptimizer."""
        optimizer = Mock()
        # Мокаем создание маршрута
        mock_route = Mock(spec=Route)
        mock_route.total_distance = 500.0
        mock_route.estimated_duration = timedelta(hours=5)
        mock_route.empty_run_distance = 0.0
        mock_route.to_dict.return_value = {"test": "route"}
        optimizer.optimize_route.return_value = mock_route
        return optimizer

    @pytest.fixture
    def mock_profitability_calculator(self):
        """Мок для ProfitabilityCalculator."""
        calculator = Mock()
        calculator.calculate.return_value = Mock(rate_per_km=0.5, total_cost=200.0)
        return calculator

    @pytest.fixture
    def mock_cargo_repository(self):
        """Мок для CargoRepository."""
        repo = Mock()
        # Мокаем груз
        mock_cargo = Mock()
        mock_cargo.id = "cargo1"
        mock_cargo.price = 1000.0
        mock_cargo.distance_osm = 500
        mock_cargo.weight = 1000
        mock_cargo.body_type = "truck"
        mock_cargo.loading_place = {
            "coordinates": {"latitude": 50.0, "longitude": 20.0},
            "city": "Warsaw",
            "country": "Poland"
        }
        mock_cargo.unloading_place = {
            "coordinates": {"latitude": 52.0, "longitude": 21.0},
            "city": "Berlin",
            "country": "Germany"
        }
        mock_cargo.loading_date = datetime(2024, 1, 1).date()
        mock_cargo.unloading_date = datetime(2024, 1, 2).date()

        repo.get_by_ids.return_value = [mock_cargo]
        repo.get_by_id.return_value = mock_cargo
        return repo

    @pytest.fixture
    def mock_vehicle_repository(self):
        """Мок для VehicleRepository."""
        repo = Mock()
        # Мокаем транспортное средство
        mock_vehicle = Mock()
        mock_vehicle.id = "vehicle1"
        mock_vehicle.max_weight = 2000
        mock_vehicle.body_type = "truck"

        repo.get_by_ids.return_value = [mock_vehicle]
        return repo

    @pytest.fixture
    def route_planner(
        self,
        mock_route_optimizer,
        mock_profitability_calculator,
        mock_cargo_repository,
        mock_vehicle_repository
    ):
        """Фикстура для RoutePlanner."""
        return RoutePlanner(
            route_optimizer=mock_route_optimizer,
            profitability_calculator=mock_profitability_calculator,
            cargo_repository=mock_cargo_repository,
            vehicle_repository=mock_vehicle_repository
        )

    def test_plan_routes_success(self, route_planner):
        """Тест успешного планирования маршрутов."""
        cargo_ids = ["cargo1"]
        vehicle_ids = ["vehicle1"]
        planning_date = datetime(2024, 1, 1)

        result = route_planner.plan_routes(cargo_ids, vehicle_ids, planning_date)

        assert isinstance(result, RoutePlanningResult)
        assert len(result.planned_routes) == 1
        assert len(result.unassigned_cargos) == 0
        assert result.total_profit > 0

        planned_route = result.planned_routes[0]
        assert planned_route.vehicle_id == "vehicle1"
        assert planned_route.assigned_cargos == ["cargo1"]
        assert planned_route.total_profit > 0

    def test_plan_routes_no_compatible_vehicles(self, route_planner, mock_vehicle_repository):
        """Тест когда нет совместимых транспортных средств."""
        # Настроим ТС как несовместимое
        mock_vehicle = Mock()
        mock_vehicle.id = "vehicle1"
        mock_vehicle.max_weight = 500  # Меньше веса груза
        mock_vehicle.body_type = "van"  # Другой тип кузова
        mock_vehicle_repository.get_by_ids.return_value = [mock_vehicle]

        cargo_ids = ["cargo1"]
        vehicle_ids = ["vehicle1"]
        planning_date = datetime(2024, 1, 1)

        result = route_planner.plan_routes(cargo_ids, vehicle_ids, planning_date)

        assert len(result.planned_routes) == 0
        assert len(result.unassigned_cargos) == 1
        assert result.unassigned_cargos == ["cargo1"]

    def test_plan_routes_multiple_cargos(self, route_planner, mock_cargo_repository):
        """Тест планирования с несколькими грузами."""
        # Добавим второй груз
        mock_cargo2 = Mock()
        mock_cargo2.id = "cargo2"
        mock_cargo2.price = 800.0
        mock_cargo2.distance_osm = 400
        mock_cargo2.weight = 800
        mock_cargo2.body_type = "truck"
        mock_cargo2.loading_place = {
            "coordinates": {"latitude": 48.0, "longitude": 2.0},
            "city": "Paris",
            "country": "France"
        }
        mock_cargo2.unloading_place = {
            "coordinates": {"latitude": 50.0, "longitude": 20.0},
            "city": "Warsaw",
            "country": "Poland"
        }

        mock_cargo_repository.get_by_ids.return_value = [mock_cargo_repository.get_by_id.return_value, mock_cargo2]
        mock_cargo_repository.get_by_id.side_effect = lambda x: {
            "cargo1": mock_cargo_repository.get_by_id.return_value,
            "cargo2": mock_cargo2
        }.get(x)

        cargo_ids = ["cargo1", "cargo2"]
        vehicle_ids = ["vehicle1"]
        planning_date = datetime(2024, 1, 1)

        result = route_planner.plan_routes(cargo_ids, vehicle_ids, planning_date)

        assert len(result.planned_routes) == 1
        assert len(result.unassigned_cargos) == 0  # Оба груза назначены
        assert len(result.planned_routes[0].assigned_cargos) == 2

    def test_is_cargo_compatible_with_vehicle(self, route_planner):
        """Тест проверки совместимости груза и ТС."""
        # Совместимый груз и ТС
        mock_cargo = Mock()
        mock_cargo.weight = 1000
        mock_cargo.body_type = "truck"

        mock_vehicle = Mock()
        mock_vehicle.max_weight = 2000
        mock_vehicle.body_type = "truck"

        assert route_planner._is_cargo_compatible_with_vehicle(mock_cargo, mock_vehicle)

        # Несовместимый по весу
        mock_vehicle.max_weight = 500
        assert not route_planner._is_cargo_compatible_with_vehicle(mock_cargo, mock_vehicle)

        # Несовместимый по типу кузова
        mock_vehicle.max_weight = 2000
        mock_vehicle.body_type = "van"
        assert not route_planner._is_cargo_compatible_with_vehicle(mock_cargo, mock_vehicle)

    def test_calculate_route_profit(self, route_planner, mock_route_optimizer):
        """Тест расчета прибыли маршрута."""
        mock_route = Mock()
        mock_route.total_distance = 500.0
        mock_route.empty_run_distance = 50.0

        cargo_ids = ["cargo1"]
        profit = route_planner._calculate_route_profit(mock_route, cargo_ids)

        assert profit > 0
        # Проверим, что profitability_calculator был вызван
        route_planner.profitability_calculator.calculate.assert_called()