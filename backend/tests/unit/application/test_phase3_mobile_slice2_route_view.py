from importlib import import_module
import inspect
from unittest.mock import Mock

import pytest


@pytest.mark.requirement_id("FR-UI-006")
@pytest.mark.test_id("TST-FR-UI-006-MOB-AT-S2")
def test_fr_ui_006_mobile_route_view_use_case_contract_exists():
    module = import_module("backend.src.application.use_cases.mobile.view_selected_cargo_route")
    use_case = getattr(module, "ViewSelectedCargoRouteUseCase")
    assert inspect.isclass(use_case)
    assert hasattr(use_case, "execute")


@pytest.mark.requirement_id("FR-UI-006")
@pytest.mark.test_id("TST-FR-UI-006-MOB-INTEG-S2")
def test_fr_ui_006_route_view_depends_on_route_projection_port():
    module = import_module("backend.src.application.use_cases.mobile.view_selected_cargo_route")
    use_case = getattr(module, "ViewSelectedCargoRouteUseCase")
    init_signature = inspect.signature(use_case.__init__)
    init_params = set(init_signature.parameters.keys())
    assert "route_projection_port" in init_params


@pytest.mark.requirement_id("FR-UI-006")
@pytest.mark.test_id("TST-FR-UI-006-MOB-INTEG-S2-FALLBACK")
def test_fr_ui_006_route_view_falls_back_to_empty_points():
    module = import_module("backend.src.application.use_cases.mobile.view_selected_cargo_route")
    use_case_cls = getattr(module, "ViewSelectedCargoRouteUseCase")

    projection_port = Mock()
    projection_port.get_route_projection.return_value = {"cargo_id": "cargo-1"}

    use_case = use_case_cls(route_projection_port=projection_port)
    result = use_case.execute(cargo_id="cargo-1")

    assert result.cargo_id == "cargo-1"
    assert result.route_points == []
