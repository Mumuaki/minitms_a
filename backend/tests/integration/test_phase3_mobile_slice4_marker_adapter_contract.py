from importlib import import_module

import pytest


@pytest.mark.requirement_id("FR-SCRAPE-004")
@pytest.mark.test_id("TST-FR-SCRAPE-004-MOB-INTEG-S4")
def test_fr_scrape_004_mobile_marker_projection_adapter_contract_exists():
    module = import_module("backend.src.infrastructure.external_services.mobile.marker_projection_adapter")
    adapter = getattr(module, "MarkerProjectionAdapter")
    assert hasattr(adapter, "get_markers")
