from importlib import import_module

import pytest


@pytest.mark.requirement_id("FR-SETTINGS-003")
@pytest.mark.test_id("TST-FR-SETTINGS-003-MOB-E2E-S6")
def test_fr_settings_003_threshold_update_flow_contains_before_after_values():
    module = import_module("backend.src.application.orchestration.mobile_e2e_flows")
    flow_cls = getattr(module, "MobileThresholdUpdateFlow")
    result = flow_cls().run()

    assert "before" in result
    assert "after" in result
    assert result["after"] >= result["before"]
