from importlib import import_module
import inspect

import pytest


@pytest.mark.requirement_id("FR-CALC-005")
@pytest.mark.test_id("TST-FR-CALC-005-MOB-AT-S3")
def test_fr_calc_005_mobile_threshold_surface_use_case_contract_exists():
    module = import_module("backend.src.application.use_cases.mobile.get_mobile_profitability_threshold")
    use_case = getattr(module, "GetMobileProfitabilityThresholdUseCase")
    assert inspect.isclass(use_case)
    assert hasattr(use_case, "execute")


@pytest.mark.requirement_id("FR-CALC-005")
@pytest.mark.test_id("TST-FR-CALC-005-MOB-INTEG-S3")
def test_fr_calc_005_mobile_threshold_surface_depends_on_settings_provider_port():
    module = import_module("backend.src.application.use_cases.mobile.get_mobile_profitability_threshold")
    use_case = getattr(module, "GetMobileProfitabilityThresholdUseCase")
    init_signature = inspect.signature(use_case.__init__)
    init_params = set(init_signature.parameters.keys())
    assert "settings_provider_port" in init_params
