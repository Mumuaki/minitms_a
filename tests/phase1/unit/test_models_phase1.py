import time

import pytest

from phase1.models import Vehicle


@pytest.mark.requirement_id("NFR-RELIAB-001")
@pytest.mark.test_id("TST-NFR-RELIAB-001-UNIT")
def test_vehicle_created_at_is_per_instance():
    first = Vehicle(
        plate_number="SK100AA",
        body_type="Box",
        length_m=13.6,
        width_m=2.45,
        height_m=2.7,
        max_weight_kg=24000,
        status="FREE",
    )
    time.sleep(0.001)
    second = Vehicle(
        plate_number="SK101AA",
        body_type="Box",
        length_m=13.6,
        width_m=2.45,
        height_m=2.7,
        max_weight_kg=24000,
        status="FREE",
    )
    assert second.created_at > first.created_at
