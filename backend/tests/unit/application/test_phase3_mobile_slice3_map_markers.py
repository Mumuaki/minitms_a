from importlib import import_module
import inspect

import pytest


@pytest.mark.requirement_id("FR-SCRAPE-004")
@pytest.mark.test_id("TST-FR-SCRAPE-004-MOB-AT-S3")
def test_fr_scrape_004_mobile_map_markers_use_case_contract_exists():
    module = import_module("backend.src.application.use_cases.mobile.get_mobile_map_markers")
    use_case = getattr(module, "GetMobileMapMarkersUseCase")
    assert inspect.isclass(use_case)
    assert hasattr(use_case, "execute")


@pytest.mark.requirement_id("FR-SCRAPE-004")
@pytest.mark.test_id("TST-FR-SCRAPE-004-MOB-INTEG-S3")
def test_fr_scrape_004_mobile_map_markers_depends_on_projection_port():
    module = import_module("backend.src.application.use_cases.mobile.get_mobile_map_markers")
    use_case = getattr(module, "GetMobileMapMarkersUseCase")
    init_signature = inspect.signature(use_case.__init__)
    init_params = set(init_signature.parameters.keys())
    assert "marker_projection_port" in init_params
