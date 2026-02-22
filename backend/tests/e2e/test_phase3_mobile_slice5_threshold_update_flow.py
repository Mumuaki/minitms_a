from importlib import import_module

import pytest


@pytest.mark.requirement_id("FR-SETTINGS-003")
@pytest.mark.test_id("TST-FR-SETTINGS-003-MOB-E2E-S5")
def test_fr_settings_003_mobile_threshold_update_flow_contract_exists():
    module = import_module("backend.src.application.orchestration.mobile_e2e_flows")
    flow = getattr(module, "MobileThresholdUpdateFlow")
    assert hasattr(flow, "run")
