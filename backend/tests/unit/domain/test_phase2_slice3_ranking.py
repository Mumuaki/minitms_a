from datetime import datetime
from unittest.mock import Mock

import pytest

from backend.src.domain.services.route_planner import RoutePlanner


@pytest.mark.requirement_id("FR-CALC-004")
@pytest.mark.test_id("TST-FR-CALC-004-WEB-AT-S3")
def test_fr_calc_004_route_planner_assigns_higher_profitability_first():
    route_optimizer = Mock()
    profitability_calculator = Mock()
    cargo_repo = Mock()
    vehicle_repo = Mock()

    cargo_high = Mock()
    cargo_high.id = "cargo-high"
    cargo_high.price = 1000.0
    cargo_high.distance_osm = 100.0
    cargo_high.weight = 1.0
    cargo_high.body_type = "truck"
    cargo_high.loading_place = {"coordinates": {"latitude": 50.0, "longitude": 20.0}, "city": "A", "country": "PL"}
    cargo_high.unloading_place = {"coordinates": {"latitude": 51.0, "longitude": 21.0}, "city": "B", "country": "DE"}
    cargo_high.loading_date = datetime(2026, 2, 13).date()
    cargo_high.unloading_date = datetime(2026, 2, 14).date()

    cargo_low = Mock()
    cargo_low.id = "cargo-low"
    cargo_low.price = 100.0
    cargo_low.distance_osm = 100.0
    cargo_low.weight = 1.0
    cargo_low.body_type = "truck"
    cargo_low.loading_place = {"coordinates": {"latitude": 52.0, "longitude": 22.0}, "city": "C", "country": "PL"}
    cargo_low.unloading_place = {"coordinates": {"latitude": 53.0, "longitude": 23.0}, "city": "D", "country": "DE"}
    cargo_low.loading_date = datetime(2026, 2, 13).date()
    cargo_low.unloading_date = datetime(2026, 2, 14).date()

    vehicle = Mock()
    vehicle.id = "vehicle-1"
    vehicle.max_weight = 10.0
    vehicle.body_type = "truck"

    cargo_repo.get_by_ids.return_value = [cargo_low, cargo_high]
    cargo_repo.get_by_id.side_effect = lambda cargo_id: {"cargo-low": cargo_low, "cargo-high": cargo_high}[cargo_id]
    vehicle_repo.get_by_ids.return_value = [vehicle]

    def profitability_side_effect(*, cargo_price, distance, empty_run_distance=None):
        if cargo_price == 1000.0:
            return Mock(rate_per_km=5.0)
        if cargo_price == 100.0:
            return Mock(rate_per_km=1.0)
        return Mock(rate_per_km=0.0)

    profitability_calculator.calculate.side_effect = profitability_side_effect

    route = Mock()
    route.total_distance = 100.0
    route.empty_run_distance = 0.0
    route.estimated_duration = datetime.now() - datetime.now()
    route_optimizer.optimize_route.return_value = route

    planner = RoutePlanner(route_optimizer, profitability_calculator, cargo_repo, vehicle_repo)

    result = planner.plan_routes(
        available_cargo_ids=["cargo-low", "cargo-high"],
        available_vehicle_ids=["vehicle-1"],
        planning_date=datetime(2026, 2, 13, 10, 0, 0),
        max_cargos_per_route=1,
    )

    assert len(result.planned_routes) == 1
    assert result.planned_routes[0].assigned_cargos == ["cargo-high"]
