import pytest

from backend.src.domain.entities.vehicle import VehicleStatus


@pytest.mark.requirement_id("FR-FLEET-003")
@pytest.mark.test_id("TST-FR-FLEET-003-WEB-AT-S2")
def test_fr_fleet_003_allowed_vehicle_statuses_are_explicit():
    actual = {status.value for status in VehicleStatus}
    assert actual == {"Free", "In Transit", "Maintenance", "Unavailable"}
