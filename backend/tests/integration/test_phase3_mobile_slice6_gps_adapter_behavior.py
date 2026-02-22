from importlib import import_module

import pytest


@pytest.mark.requirement_id("FR-FLEET-002")
@pytest.mark.test_id("TST-FR-FLEET-002-MOB-INTEG-S6")
def test_fr_fleet_002_gps_adapter_returns_non_empty_positions_with_freshness():
    module = import_module("backend.src.infrastructure.external_services.mobile.mobile_gps_provider_adapter")
    adapter_cls = getattr(module, "MobileGpsProviderAdapter")
    adapter = adapter_cls()

    positions = adapter.get_positions()
    assert len(positions) > 0
    assert all("vehicle_id" in p and "freshness_seconds" in p for p in positions)
