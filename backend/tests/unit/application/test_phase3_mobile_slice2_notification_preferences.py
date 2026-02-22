from importlib import import_module
import inspect
from unittest.mock import Mock

import pytest


@pytest.mark.requirement_id("FR-NOTIFY-003")
@pytest.mark.test_id("TST-FR-NOTIFY-003-MOB-AT-S2")
def test_fr_notify_003_mobile_notification_preferences_use_case_contract_exists():
    module = import_module("backend.src.application.use_cases.mobile.update_notification_preferences")
    use_case = getattr(module, "UpdateMobileNotificationPreferencesUseCase")
    assert inspect.isclass(use_case)
    assert hasattr(use_case, "execute")


@pytest.mark.requirement_id("FR-NOTIFY-003")
@pytest.mark.test_id("TST-FR-NOTIFY-003-MOB-INTEG-S2")
def test_fr_notify_003_preferences_use_case_depends_on_repository_port():
    module = import_module("backend.src.application.use_cases.mobile.update_notification_preferences")
    use_case = getattr(module, "UpdateMobileNotificationPreferencesUseCase")
    init_signature = inspect.signature(use_case.__init__)
    init_params = set(init_signature.parameters.keys())
    assert "preferences_repository_port" in init_params


@pytest.mark.requirement_id("FR-NOTIFY-003")
@pytest.mark.test_id("TST-FR-NOTIFY-003-MOB-INTEG-S2-ERROR")
def test_fr_notify_003_preferences_repository_error_is_propagated():
    module = import_module("backend.src.application.use_cases.mobile.update_notification_preferences")
    use_case_cls = getattr(module, "UpdateMobileNotificationPreferencesUseCase")

    repo = Mock()
    repo.save_preferences.side_effect = RuntimeError("storage unavailable")
    use_case = use_case_cls(preferences_repository_port=repo)

    with pytest.raises(RuntimeError):
        use_case.execute(user_id="user-1", preferences={"push_enabled": True})
