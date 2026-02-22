from importlib import import_module
import inspect
from unittest.mock import Mock

import pytest


@pytest.mark.requirement_id("FR-SETTINGS-003")
@pytest.mark.test_id("TST-FR-SETTINGS-003-MOB-UNIT-S3")
def test_fr_settings_003_mobile_threshold_validator_contract_exists():
    module = import_module("backend.src.application.use_cases.mobile.update_mobile_profitability_threshold")
    validator = getattr(module, "MobileThresholdValidator")
    assert inspect.isclass(validator)
    assert hasattr(validator, "validate")


@pytest.mark.requirement_id("FR-SETTINGS-003")
@pytest.mark.test_id("TST-FR-SETTINGS-003-MOB-INTEG-S3")
def test_fr_settings_003_mobile_threshold_update_depends_on_settings_repository_port():
    module = import_module("backend.src.application.use_cases.mobile.update_mobile_profitability_threshold")
    use_case = getattr(module, "UpdateMobileProfitabilityThresholdUseCase")
    init_signature = inspect.signature(use_case.__init__)
    init_params = set(init_signature.parameters.keys())
    assert "settings_repository_port" in init_params


@pytest.mark.requirement_id("FR-SETTINGS-003")
@pytest.mark.test_id("TST-FR-SETTINGS-003-MOB-UNIT-S3-BOUNDARIES")
def test_fr_settings_003_mobile_threshold_validator_accepts_boundaries():
    module = import_module("backend.src.application.use_cases.mobile.update_mobile_profitability_threshold")
    validator = getattr(module, "MobileThresholdValidator")
    assert validator.validate(0.15) == 0.15
    assert validator.validate(3.5) == 3.5


@pytest.mark.requirement_id("FR-SETTINGS-003")
@pytest.mark.test_id("TST-FR-SETTINGS-003-MOB-INTEG-S3-INVALID-TYPE")
def test_fr_settings_003_mobile_threshold_update_rejects_invalid_type():
    module = import_module("backend.src.application.use_cases.mobile.update_mobile_profitability_threshold")
    use_case_cls = getattr(module, "UpdateMobileProfitabilityThresholdUseCase")

    repo = Mock()
    use_case = use_case_cls(settings_repository_port=repo)

    with pytest.raises(ValueError):
        use_case.execute(value="not-a-number")
