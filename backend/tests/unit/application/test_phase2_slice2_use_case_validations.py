import pytest

from backend.src.application.use_cases.fleet.update_vehicle_status import UpdateVehicleStatusUseCase
from backend.src.application.use_cases.orders.sync_to_google_sheets import SyncToGoogleSheetsUseCase
from backend.src.domain.entities.vehicle import VehicleStatus


@pytest.mark.requirement_id("FR-FLEET-003")
@pytest.mark.test_id("TST-FR-FLEET-003-WEB-UNIT-VALIDATION-S2")
def test_fr_fleet_003_vehicle_status_rejects_invalid_value():
    with pytest.raises(ValueError, match="status must be a valid VehicleStatus value"):
        UpdateVehicleStatusUseCase().execute(vehicle_id=1, status="INVALID")


@pytest.mark.requirement_id("FR-FLEET-003")
@pytest.mark.test_id("TST-FR-FLEET-003-WEB-UNIT-OK-S2")
def test_fr_fleet_003_vehicle_status_accepts_valid_value():
    result = UpdateVehicleStatusUseCase().execute(vehicle_id=1, status=VehicleStatus.FREE.value)
    assert result["status"] == VehicleStatus.FREE.value


@pytest.mark.requirement_id("BR-022")
@pytest.mark.test_id("TST-BR-022-WEB-UNIT-VALIDATION-S2")
def test_br_022_sync_payload_must_be_dict():
    with pytest.raises(ValueError, match="payload must be a dictionary"):
        SyncToGoogleSheetsUseCase().execute(order_id=10, payload="not-a-dict")
