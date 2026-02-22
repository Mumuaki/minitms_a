from importlib import import_module

import pytest


@pytest.mark.requirement_id("FR-CALC-005")
@pytest.mark.test_id("TST-FR-CALC-005-MOB-INTEG-S4")
def test_fr_calc_005_mobile_settings_provider_adapter_contract_exists():
    module = import_module("backend.src.infrastructure.external_services.mobile.mobile_settings_provider_adapter")
    adapter = getattr(module, "MobileSettingsProviderAdapter")
    assert hasattr(adapter, "get_min_acceptable_rate")


@pytest.mark.requirement_id("FR-CALC-005")
@pytest.mark.test_id("TST-FR-CALC-005-MOB-INTEG-S4-WRITE")
def test_fr_calc_005_mobile_settings_repository_adapter_contract_exists():
    module = import_module("backend.src.infrastructure.external_services.mobile.mobile_settings_repository_adapter")
    adapter = getattr(module, "MobileSettingsRepositoryAdapter")
    assert hasattr(adapter, "save_min_acceptable_rate")

    instance = adapter()
    saved = instance.save_min_acceptable_rate(value=0.77)
    assert saved == 0.77
    assert instance._last_saved_min_acceptable_rate == 0.77
