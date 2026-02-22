from importlib import import_module

import pytest


@pytest.mark.requirement_id("FR-UI-006")
@pytest.mark.test_id("TST-FR-UI-006-MOB-E2E-S5")
def test_fr_ui_006_mobile_login_list_map_flow_contract_exists():
    module = import_module("backend.src.application.orchestration.mobile_e2e_flows")
    flow = getattr(module, "MobileLoginListMapFlow")
    assert hasattr(flow, "run")
