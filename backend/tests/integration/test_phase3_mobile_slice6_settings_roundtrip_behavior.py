from importlib import import_module

import pytest


@pytest.mark.requirement_id("FR-CALC-005")
@pytest.mark.test_id("TST-FR-CALC-005-MOB-INTEG-S6")
def test_fr_calc_005_settings_roundtrip_between_repository_and_provider():
    provider_module = import_module(
        "backend.src.infrastructure.external_services.mobile.mobile_settings_provider_adapter"
    )
    repository_module = import_module(
        "backend.src.infrastructure.external_services.mobile.mobile_settings_repository_adapter"
    )
    settings_module = import_module("backend.src.infrastructure.config.settings")

    settings = getattr(settings_module, "Settings")()
    provider = getattr(provider_module, "MobileSettingsProviderAdapter")(settings=settings)
    repository = getattr(repository_module, "MobileSettingsRepositoryAdapter")(settings=settings)

    repository.save_min_acceptable_rate(value=0.91)
    assert provider.get_min_acceptable_rate() == 0.91
