from importlib import import_module

import pytest


@pytest.mark.requirement_id("FR-UI-006")
@pytest.mark.test_id("TST-FR-UI-006-MOB-E2E-S6")
def test_fr_ui_006_login_list_map_flow_contains_step_trace():
    module = import_module("backend.src.application.orchestration.mobile_e2e_flows")
    flow_cls = getattr(module, "MobileLoginListMapFlow")
    result = flow_cls().run()

    assert "steps" in result
    assert result["steps"] == ["login", "list", "map"]
