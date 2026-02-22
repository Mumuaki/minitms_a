import pytest

from backend.src.infrastructure.config.settings import Settings


@pytest.mark.requirement_id("FR-CALC-005")
@pytest.mark.test_id("TST-FR-CALC-005-WEB-AT-S3")
def test_fr_calc_005_settings_exposes_min_acceptable_rate():
    settings = Settings()
    assert hasattr(settings, "MIN_ACCEPTABLE_RATE")


@pytest.mark.requirement_id("FR-CALC-005")
@pytest.mark.test_id("TST-FR-CALC-005-WEB-INTEG-S3")
def test_fr_calc_005_min_acceptable_rate_integrates_with_runtime_validation():
    with pytest.raises(ValueError):
        Settings(MIN_ACCEPTABLE_RATE=0.1)


@pytest.mark.requirement_id("FR-SETTINGS-003")
@pytest.mark.test_id("TST-FR-SETTINGS-003-WEB-UNIT-S3")
def test_fr_settings_003_min_acceptable_rate_validated_range():
    with pytest.raises(ValueError):
        Settings(MIN_ACCEPTABLE_RATE=4.0)
