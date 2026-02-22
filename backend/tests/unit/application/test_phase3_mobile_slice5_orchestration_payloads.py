from backend.src.application.orchestration.mobile_e2e_flows import (
    MobileLoginListMapFlow,
    MobileThresholdUpdateFlow,
)


def test_mobile_login_list_map_flow_run_payload_shape():
    result = MobileLoginListMapFlow().run()
    assert result["flow"] == "login_list_map"
    assert result["status"] == "ready"


def test_mobile_threshold_update_flow_run_payload_shape():
    result = MobileThresholdUpdateFlow().run()
    assert result["flow"] == "threshold_update"
    assert result["status"] == "ready"
