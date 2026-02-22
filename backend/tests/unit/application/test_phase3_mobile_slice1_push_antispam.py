from importlib import import_module
import inspect

import pytest


@pytest.mark.requirement_id("FR-NOTIFY-004")
@pytest.mark.test_id("TST-FR-NOTIFY-004-MOB-AT-S1")
def test_fr_notify_004_push_antispam_use_case_contract_exists():
    module = import_module("backend.src.application.use_cases.notifications.dispatch_mobile_push")
    use_case = getattr(module, "DispatchMobilePushUseCase")
    assert inspect.isclass(use_case)
    assert hasattr(use_case, "execute")

    init_signature = inspect.signature(use_case.__init__)
    init_params = set(init_signature.parameters.keys())
    assert "push_gateway_port" in init_params
    assert "cooldown_policy_port" in init_params


@pytest.mark.requirement_id("FR-NOTIFY-004")
@pytest.mark.test_id("TST-FR-NOTIFY-004-MOB-INTEG-S1")
def test_fr_notify_004_push_gateway_integration_port_exists():
    module = import_module("backend.src.application.ports.mobile_push_gateway_port")
    port = getattr(module, "MobilePushGatewayPort")
    assert inspect.isclass(port)
    assert hasattr(port, "send")


@pytest.mark.requirement_id("BR-014")
@pytest.mark.test_id("TST-BR-014-MOB-UNIT-S1")
def test_br_014_mobile_push_cooldown_constant_present():
    settings_module = import_module("backend.src.infrastructure.config.settings")
    settings = getattr(settings_module, "Settings")()
    assert hasattr(settings, "MOBILE_PUSH_COOLDOWN_SECONDS")
    assert settings.MOBILE_PUSH_COOLDOWN_SECONDS >= 300
