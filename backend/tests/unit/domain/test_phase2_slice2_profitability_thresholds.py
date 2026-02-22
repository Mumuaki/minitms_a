import pytest

from backend.src.domain.services.profitability_calculator import ProfitabilityCalculator
from backend.src.domain.value_objects.profitability import ProfitabilityStatus


@pytest.mark.requirement_id("BR-011")
@pytest.mark.test_id("TST-BR-011-WEB-UNIT-S2")
def test_br_011_gray_threshold_for_054_to_059():
    result = ProfitabilityCalculator().calculate(cargo_price=5.5, distance=10.0, empty_run_distance=0.0)
    assert result.rate_per_km == pytest.approx(0.55)
    assert result.status_color == ProfitabilityStatus.GRAY


@pytest.mark.requirement_id("BR-012")
@pytest.mark.test_id("TST-BR-012-WEB-UNIT-S2")
def test_br_012_yellow_threshold_for_060_to_079():
    result = ProfitabilityCalculator().calculate(cargo_price=7.0, distance=10.0, empty_run_distance=0.0)
    assert result.rate_per_km == pytest.approx(0.7)
    assert result.status_color == ProfitabilityStatus.YELLOW


@pytest.mark.requirement_id("BR-013")
@pytest.mark.test_id("TST-BR-013-WEB-UNIT-S2")
def test_br_013_green_threshold_for_080_and_above():
    result = ProfitabilityCalculator().calculate(cargo_price=8.0, distance=10.0, empty_run_distance=0.0)
    assert result.rate_per_km == pytest.approx(0.8)
    assert result.status_color == ProfitabilityStatus.GREEN
