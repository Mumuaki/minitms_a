import importlib
import inspect

import pytest


@pytest.mark.requirement_id("FR-FLEET-003")
@pytest.mark.test_id("TST-FR-FLEET-003-WEB-INTEG-S2")
def test_fr_fleet_003_update_status_use_case_contract_exists():
    module = importlib.import_module("backend.src.application.use_cases.fleet.update_vehicle_status")
    assert hasattr(module, "UpdateVehicleStatusUseCase")
    use_case_cls = getattr(module, "UpdateVehicleStatusUseCase")
    assert inspect.isclass(use_case_cls)
    assert hasattr(use_case_cls, "execute")


@pytest.mark.requirement_id("BR-022")
@pytest.mark.test_id("TST-BR-022-WEB-INTEG-S2")
def test_br_022_sheets_sync_use_case_contract_exists():
    module = importlib.import_module("backend.src.application.use_cases.orders.sync_to_google_sheets")
    assert hasattr(module, "SyncToGoogleSheetsUseCase")
    use_case_cls = getattr(module, "SyncToGoogleSheetsUseCase")
    assert inspect.isclass(use_case_cls)
    assert hasattr(use_case_cls, "execute")


@pytest.mark.requirement_id("BR-015")
@pytest.mark.test_id("TST-BR-015-WEB-INTEG-S2")
def test_br_015_smtp_client_contract_exists():
    module = importlib.import_module("backend.src.infrastructure.external_services.smtp.email_client")
    assert hasattr(module, "EmailClient")
    client_cls = getattr(module, "EmailClient")
    assert inspect.isclass(client_cls)
    assert hasattr(client_cls, "send")
