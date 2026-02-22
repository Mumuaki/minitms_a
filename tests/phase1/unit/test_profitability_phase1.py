import pytest

from phase1.profitability import (
    ColorStatus,
    apply_min_threshold,
    classify_rate,
    ensure_min_distance,
    filter_for_vehicle,
    gross_rate_per_km,
    rank_cargos,
)

@pytest.mark.requirement_id("FR-CALC-001")
@pytest.mark.test_id("TST-FR-CALC-001-UNIT")
def test_fr_calc_001_vehicle_compatibility_filter(sample_cargos, sample_vehicle):
    compatible = filter_for_vehicle(sample_cargos, sample_vehicle)
    assert [c.cargo_id for c in compatible] == ["C1"]


@pytest.mark.requirement_id("FR-CALC-003")
@pytest.mark.test_id("TST-FR-CALC-003-UNIT")
def test_fr_calc_003_gross_rate_formula():
    rate = gross_rate_per_km(1000.0, 100.0, 400.0)
    assert rate == pytest.approx(2.0)


@pytest.mark.requirement_id("FR-CALC-004")
@pytest.mark.test_id("TST-FR-CALC-004-UNIT")
def test_fr_calc_004_descending_rate_ranking(sample_cargos):
    ranked = rank_cargos(sample_cargos, distance_a_b_km=100.0)
    assert ranked[0].gross_rate_per_km >= ranked[1].gross_rate_per_km


@pytest.mark.requirement_id("FR-CALC-005")
@pytest.mark.test_id("TST-FR-CALC-005-UNIT")
def test_fr_calc_005_user_min_rate_threshold(sample_cargos):
    ranked = rank_cargos(sample_cargos, distance_a_b_km=100.0)
    filtered = apply_min_threshold(ranked, min_rate=2.0)
    assert all(item.gross_rate_per_km >= 2.0 for item in filtered)


@pytest.mark.requirement_id("BR-006")
@pytest.mark.test_id("TST-BR-006-UNIT")
def test_br_006_rate_formula_rule():
    assert gross_rate_per_km(500.0, 50.0, 50.0) == pytest.approx(5.0)


@pytest.mark.requirement_id("BR-007")
@pytest.mark.test_id("TST-BR-007-UNIT")
def test_br_007_exclude_incompatible_cargo(sample_cargos, sample_vehicle):
    compatible = filter_for_vehicle(sample_cargos, sample_vehicle)
    assert len(compatible) == 1


@pytest.mark.requirement_id("BR-009")
@pytest.mark.test_id("TST-BR-009-UNIT")
def test_br_009_min_distance_floor():
    assert ensure_min_distance(2.0) == 10.0
    assert ensure_min_distance(20.0) == 20.0


@pytest.mark.requirement_id("BR-010")
@pytest.mark.test_id("TST-BR-010-UNIT")
def test_br_010_red_threshold():
    assert classify_rate(0.53) == ColorStatus.RED


@pytest.mark.requirement_id("BR-011")
@pytest.mark.test_id("TST-BR-011-UNIT")
def test_br_011_gray_threshold():
    assert classify_rate(0.54) == ColorStatus.GRAY
    assert classify_rate(0.59) == ColorStatus.GRAY


@pytest.mark.requirement_id("BR-012")
@pytest.mark.test_id("TST-BR-012-UNIT")
def test_br_012_yellow_threshold():
    assert classify_rate(0.60) == ColorStatus.YELLOW
    assert classify_rate(0.79) == ColorStatus.YELLOW


@pytest.mark.requirement_id("BR-013")
@pytest.mark.test_id("TST-BR-013-UNIT")
def test_br_013_green_threshold():
    assert classify_rate(0.80) == ColorStatus.GREEN
