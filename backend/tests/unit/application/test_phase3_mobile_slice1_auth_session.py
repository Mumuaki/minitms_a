from importlib import import_module
import inspect
from unittest.mock import Mock

import pytest


@pytest.mark.requirement_id("FR-AUTH-001")
@pytest.mark.test_id("TST-FR-AUTH-001-MOB-AT-S1")
def test_fr_auth_001_mobile_auth_use_case_contract_exists():
    module = import_module("backend.src.application.use_cases.mobile.authenticate_mobile_user")
    use_case = getattr(module, "AuthenticateMobileUserUseCase")
    assert inspect.isclass(use_case)
    assert hasattr(use_case, "execute")


@pytest.mark.requirement_id("FR-AUTH-001")
@pytest.mark.test_id("TST-FR-AUTH-001-MOB-INTEG-S1")
def test_fr_auth_001_mobile_auth_depends_on_session_bootstrap_contract():
    module = import_module("backend.src.application.use_cases.mobile.authenticate_mobile_user")
    use_case = getattr(module, "AuthenticateMobileUserUseCase")
    init_signature = inspect.signature(use_case.__init__)
    init_params = set(init_signature.parameters.keys())
    assert "session_bootstrap_port" in init_params
    assert "credential_verifier_port" in init_params

    execute_signature = inspect.signature(use_case.execute)
    execute_params = set(execute_signature.parameters.keys())
    assert "username" in execute_params
    assert "password" in execute_params
    assert "device_id" in execute_params

    verifier = Mock()
    verifier.verify_credentials.return_value = False
    bootstrap = Mock()

    auth_use_case = use_case(
        session_bootstrap_port=bootstrap,
        credential_verifier_port=verifier,
    )
    result = auth_use_case.execute(username="dispatcher", password="bad", device_id="dev-1")

    assert result.authenticated is False
    bootstrap.bootstrap_session.assert_not_called()


@pytest.mark.requirement_id("FR-AUTH-004")
@pytest.mark.test_id("TST-FR-AUTH-004-MOB-UNIT-S1")
def test_fr_auth_004_mobile_remember_me_policy_constant_present():
    settings_module = import_module("backend.src.infrastructure.config.settings")
    settings = getattr(settings_module, "Settings")()
    assert hasattr(settings, "MOBILE_REMEMBER_ME_DAYS")
    assert settings.MOBILE_REMEMBER_ME_DAYS > 0
