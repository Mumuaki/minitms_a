from importlib import import_module

import pytest


@pytest.mark.requirement_id("FR-SCRAPE-004")
@pytest.mark.test_id("TST-FR-SCRAPE-004-MOB-INTEG-S6")
def test_fr_scrape_004_marker_adapter_returns_coordinates_and_semantic_types():
    module = import_module("backend.src.infrastructure.external_services.mobile.marker_projection_adapter")
    adapter_cls = getattr(module, "MarkerProjectionAdapter")
    adapter = adapter_cls()

    markers = adapter.get_markers(cargo_id="cargo-1")
    assert len(markers) == 3

    marker_types = {item["type"] for item in markers}
    assert marker_types == {"A", "B", "C"}
    assert all("latitude" in item and "longitude" in item for item in markers)
