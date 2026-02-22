from importlib import import_module

import pytest


@pytest.mark.requirement_id("FR-FLEET-002")
@pytest.mark.test_id("TST-FR-FLEET-002-MOB-INTEG-S4")
def test_fr_fleet_002_mobile_gps_provider_adapter_contract_exists():
    module = import_module("backend.src.infrastructure.external_services.mobile.mobile_gps_provider_adapter")
    adapter = getattr(module, "MobileGpsProviderAdapter")
    assert hasattr(adapter, "get_positions")
    assert adapter.__doc__ == "Contract stub for Slice-4 integration stage."
