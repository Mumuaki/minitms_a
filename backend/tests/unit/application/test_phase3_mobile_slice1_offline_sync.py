from importlib import import_module
import inspect
from unittest.mock import Mock

import pytest


@pytest.mark.requirement_id("FR-MOB-OFFLINE-001")
@pytest.mark.test_id("TST-MOB-OFFLINE-SYNC-AT-S1")
def test_mobile_offline_sync_use_case_contract_exists():
    module = import_module("backend.src.application.use_cases.mobile.sync_offline_actions")
    use_case = getattr(module, "SyncOfflineActionsUseCase")
    assert inspect.isclass(use_case)
    assert hasattr(use_case, "execute")

    execute_signature = inspect.signature(use_case.execute)
    execute_params = set(execute_signature.parameters.keys())
    assert "device_id" in execute_params
    assert "pending_actions" in execute_params


@pytest.mark.requirement_id("FR-MOB-OFFLINE-001")
@pytest.mark.test_id("TST-MOB-OFFLINE-SYNC-INTEG-S1")
def test_mobile_offline_checkpoint_repository_contract_exists():
    module = import_module("backend.src.application.ports.mobile_offline_checkpoint_port")
    port = getattr(module, "MobileOfflineCheckpointPort")
    assert inspect.isclass(port)
    assert hasattr(port, "load_checkpoint")
    assert hasattr(port, "save_checkpoint")

    use_case_module = import_module("backend.src.application.use_cases.mobile.sync_offline_actions")
    use_case = getattr(use_case_module, "SyncOfflineActionsUseCase")

    checkpoint_port = Mock()
    checkpoint_port.load_checkpoint.return_value = "opaque-token-v1"
    sync_use_case = use_case(checkpoint_port=checkpoint_port)

    result = sync_use_case.execute(
        device_id="device-1",
        pending_actions=[{"kind": "status_update"}],
    )

    checkpoint_port.save_checkpoint.assert_called_once()
    saved_checkpoint = checkpoint_port.save_checkpoint.call_args.kwargs["checkpoint"]
    assert saved_checkpoint.startswith("opaque-token-v1|applied:")
    assert result.checkpoint == saved_checkpoint
