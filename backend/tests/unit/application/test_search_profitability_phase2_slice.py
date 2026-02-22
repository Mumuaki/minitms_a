from datetime import date
from unittest.mock import Mock

import pytest

from backend.src.application.dto.cargo_dto import (
    CargoDto,
    LocationDto,
    SearchCargoRequestDto,
    SearchCargoResponseDto,
)
from backend.src.application.use_cases.cargo.filter_by_vehicle import FilterByVehicleUseCase
from backend.src.application.use_cases.cargo.search_cargos import SearchCargosUseCase
from backend.src.domain.services.profitability_calculator import ProfitabilityCalculator
from backend.src.domain.value_objects.profitability import ProfitabilityStatus


@pytest.mark.requirement_id("FR-SCRAPE-002")
@pytest.mark.test_id("TST-FR-SCRAPE-002-WEB-INTEG")
def test_fr_scrape_002_web_filters_are_forwarded_to_search_repo():
    repo = Mock()
    repo.search_cargos.return_value = SearchCargoResponseDto(items=[], total=0, page=1, limit=20, total_pages=0)
    use_case = SearchCargosUseCase(repo, Mock())

    request = SearchCargoRequestDto(
        loading_date_from=date(2026, 2, 1),
        loading_date_to=date(2026, 2, 28),
        weight_min=5.0,
        weight_max=20.0,
        body_type="TENT",
        page=1,
        limit=20,
    )

    use_case.execute(request)

    forwarded = repo.search_cargos.call_args[0][0]
    assert forwarded.loading_date_from == date(2026, 2, 1)
    assert forwarded.loading_date_to == date(2026, 2, 28)
    assert forwarded.weight_min == 5.0
    assert forwarded.weight_max == 20.0
    assert forwarded.body_type == "TENT"


@pytest.mark.requirement_id("FR-UI-001")
@pytest.mark.test_id("TST-FR-UI-001-WEB-INTEG")
def test_fr_ui_001_web_sorting_and_pagination_are_forwarded():
    repo = Mock()
    repo.search_cargos.return_value = SearchCargoResponseDto(items=[], total=0, page=2, limit=10, total_pages=0)
    use_case = SearchCargosUseCase(repo, Mock())

    request = SearchCargoRequestDto(
        order_by="price",
        order_direction="asc",
        page=2,
        limit=10,
    )

    use_case.execute(request)

    forwarded = repo.search_cargos.call_args[0][0]
    assert forwarded.order_by == "price"
    assert forwarded.order_direction == "asc"
    assert forwarded.page == 2
    assert forwarded.limit == 10


@pytest.mark.requirement_id("FR-CALC-001")
@pytest.mark.test_id("TST-FR-CALC-001-WEB-INTEG")
def test_fr_calc_001_vehicle_constraints_are_applied_for_filter():
    repo = Mock()
    repo.search_cargos.return_value = SearchCargoResponseDto(items=[], total=0, page=1, limit=10, total_pages=0)
    use_case = FilterByVehicleUseCase(repo, Mock())

    use_case.execute(
        vehicle_body_type="TENT",
        vehicle_max_weight=12.0,
        vehicle_length=13.6,
        vehicle_width=2.45,
        vehicle_height=2.7,
        page=1,
        limit=10,
    )

    forwarded = repo.search_cargos.call_args[0][0]
    assert forwarded.vehicle_body_type == "TENT"
    assert forwarded.vehicle_max_weight == 12.0
    assert forwarded.vehicle_length == 13.6
    assert forwarded.vehicle_width == 2.45
    assert forwarded.vehicle_height == 2.7


@pytest.mark.requirement_id("FR-CALC-003")
@pytest.mark.test_id("TST-FR-CALC-003-WEB-AT")
@pytest.mark.requirement_id("BR-006")
@pytest.mark.test_id("TST-BR-006-WEB-UNIT")
def test_fr_calc_003_and_br_006_rate_formula_uses_total_distance():
    calculator = ProfitabilityCalculator()

    result = calculator.calculate(
        cargo_price=1000.0,
        distance=400.0,
        empty_run_distance=100.0,
    )

    assert result.total_distance == pytest.approx(500.0)
    assert result.rate_per_km == pytest.approx(2.0)


@pytest.mark.requirement_id("BR-007")
@pytest.mark.test_id("TST-BR-007-WEB-UNIT")
def test_br_007_vehicle_incompatible_cargo_is_excluded_by_body_type():
    cargo_ok = CargoDto(
        id="1",
        external_id="ext1",
        source="trans.eu",
        loading_place=LocationDto(address="A", country_code="DE", lat=1.0, lon=1.0),
        unloading_place=LocationDto(address="B", country_code="FR", lat=2.0, lon=2.0),
        loading_date=date(2026, 2, 1),
        unloading_date=date(2026, 2, 2),
        weight=8.0,
        body_type="TENT",
        price=900.0,
        distance_trans_eu=400,
        distance_osm=420,
        profitability=None,
        is_hidden=False,
        created_at="2026-02-01T00:00:00",
    )
    cargo_bad = CargoDto(
        id="2",
        external_id="ext2",
        source="trans.eu",
        loading_place=LocationDto(address="A", country_code="DE", lat=1.0, lon=1.0),
        unloading_place=LocationDto(address="B", country_code="FR", lat=2.0, lon=2.0),
        loading_date=date(2026, 2, 1),
        unloading_date=date(2026, 2, 2),
        weight=8.0,
        body_type="FRIGO",
        price=900.0,
        distance_trans_eu=400,
        distance_osm=420,
        profitability=None,
        is_hidden=False,
        created_at="2026-02-01T00:00:00",
    )

    class FilteringRepo:
        def search_cargos(self, request):
            items = [cargo_ok, cargo_bad]
            filtered = [item for item in items if item.body_type == request.vehicle_body_type]
            return SearchCargoResponseDto(
                items=filtered,
                total=len(filtered),
                page=request.page,
                limit=request.limit,
                total_pages=1,
            )

    result = FilterByVehicleUseCase(FilteringRepo(), Mock()).execute(
        vehicle_body_type="TENT",
        page=1,
        limit=10,
    )

    assert [item.id for item in result.items] == ["1"]


@pytest.mark.requirement_id("BR-008")
@pytest.mark.test_id("TST-BR-008-WEB-INTEG")
def test_br_008_distance_type_osm_uses_osm_distance_field():
    repo = Mock()
    repo.search_cargos.return_value = SearchCargoResponseDto(
        items=[
            CargoDto(
                id="1",
                external_id="ext1",
                source="trans.eu",
                loading_place=LocationDto(address="A", country_code="DE", lat=1.0, lon=1.0),
                unloading_place=LocationDto(address="B", country_code="FR", lat=2.0, lon=2.0),
                loading_date=date(2026, 2, 1),
                unloading_date=date(2026, 2, 2),
                weight=8.0,
                body_type="TENT",
                price=600.0,
                distance_trans_eu=100,
                distance_osm=300,
                profitability=None,
                is_hidden=False,
                created_at="2026-02-01T00:00:00",
            )
        ],
        total=1,
        page=1,
        limit=10,
        total_pages=1,
    )
    use_case = SearchCargosUseCase(repo, ProfitabilityCalculator())

    result = use_case.execute(
        SearchCargoRequestDto(
            distance_type="osm",
            fuel_price=0.0,
            page=1,
            limit=10,
        )
    )

    assert result.items[0].profitability is not None
    assert result.items[0].profitability.total_distance == pytest.approx(300.0)


@pytest.mark.requirement_id("BR-009")
@pytest.mark.test_id("TST-BR-009-WEB-UNIT")
def test_br_009_min_distance_floor_applied_to_short_routes():
    calculator = ProfitabilityCalculator()
    result = calculator.calculate(cargo_price=100.0, distance=3.0, empty_run_distance=2.0)
    assert result.total_distance == pytest.approx(10.0)
    assert result.rate_per_km == pytest.approx(10.0)


@pytest.mark.requirement_id("BR-010")
@pytest.mark.test_id("TST-BR-010-WEB-UNIT")
def test_br_010_red_threshold_classification():
    assert ProfitabilityStatus.RED == ProfitabilityStatus("RED")
    assert (
        ProfitabilityCalculator()
        .calculate(cargo_price=5.0, distance=20.0, empty_run_distance=0.0)
        .status_color
        == ProfitabilityStatus.RED
    )


@pytest.mark.requirement_id("BR-006")
@pytest.mark.test_id("TST-BR-006-WEB-UNIT-ZERO")
def test_br_006_zero_price_is_valid_not_missing():
    result = ProfitabilityCalculator().calculate(
        cargo_price=0.0,
        distance=20.0,
        empty_run_distance=0.0,
        fuel_consumption=0.0,
        fuel_price=0.0,
        depreciation_per_km=0.0,
        driver_salary_per_km=0.0,
        other_costs_per_km=0.0,
    )
    assert result.rate_per_km == pytest.approx(0.0)
    assert result.status_color == ProfitabilityStatus.RED
