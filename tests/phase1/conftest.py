import pathlib
import sys
from datetime import date
from datetime import datetime

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from phase1.models import Cargo, User, Vehicle


def pytest_configure(config):
    config.addinivalue_line("markers", "requirement_id(value): Requirement ID traceability marker")
    config.addinivalue_line("markers", "test_id(value): Test ID traceability marker")


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 2, 13, 10, 0, 0)


@pytest.fixture
def sample_user() -> User:
    return User(username="dispatcher", password="secret", role="Dispatcher")


@pytest.fixture
def sample_vehicle() -> Vehicle:
    return Vehicle(
        plate_number="SK123AA",
        body_type="Box",
        length_m=13.6,
        width_m=2.45,
        height_m=2.7,
        max_weight_kg=24000,
        status="FREE",
        location_lat=48.1486,
        location_lon=17.1077,
    )


@pytest.fixture
def sample_cargos() -> list[Cargo]:
    return [
        Cargo(
            cargo_id="C1",
            body_type="Box",
            weight_kg=10000,
            required_length_m=10.0,
            required_width_m=2.4,
            required_height_m=2.5,
            price_eur=1200.0,
            distance_b_c_km=500.0,
            loading_country="SK",
            unloading_country="PL",
            loading_date=date(2026, 2, 14),
        ),
        Cargo(
            cargo_id="C2",
            body_type="Box",
            weight_kg=26000,
            required_length_m=12.0,
            required_width_m=2.4,
            required_height_m=2.5,
            price_eur=3000.0,
            distance_b_c_km=600.0,
            loading_country="SK",
            unloading_country="DE",
            loading_date=date(2026, 2, 20),
        ),
    ]
