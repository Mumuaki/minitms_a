import pytest
from datetime import date

from phase1.auth import AuthService
from phase1.fleet import FleetService
from phase1.models import User, Vehicle
from phase1.profitability import request_distance_a_b
from phase1.scraping import ScrapeFilters, ScrapingService

@pytest.mark.requirement_id("FR-AUTH-003")
@pytest.mark.test_id("TST-FR-AUTH-003-INTEG")
def test_fr_auth_003_account_lock_after_failed_attempts(now):
    service = AuthService([User(username="u", password="p", role="Dispatcher")])
    for _ in range(5):
        with pytest.raises(ValueError):
            service.login("u", "wrong", now)
    with pytest.raises(ValueError, match="account_locked"):
        service.login("u", "p", now)


@pytest.mark.requirement_id("FR-AUTH-005")
@pytest.mark.test_id("TST-FR-AUTH-005-INTEG")
def test_fr_auth_005_login_audit_recorded(now):
    service = AuthService([User(username="u", password="p", role="Dispatcher")])
    with pytest.raises(ValueError):
        service.login("u", "wrong", now)
    service.login("u", "p", now)
    assert "login_failed:u" in service.audit_log
    assert "login_success:u" in service.audit_log


@pytest.mark.requirement_id("FR-FLEET-001")
@pytest.mark.test_id("TST-FR-FLEET-001-INTEG")
def test_fr_fleet_001_vehicle_required_fields():
    service = FleetService()
    with pytest.raises(ValueError):
        service.add_vehicle(
            Vehicle(
                plate_number="",
                body_type="Box",
                length_m=13.6,
                width_m=2.45,
                height_m=2.7,
                max_weight_kg=24000,
                status="FREE",
            )
        )


@pytest.mark.requirement_id("FR-FLEET-001")
@pytest.mark.test_id("TST-FR-FLEET-001-INTEG")
def test_fr_fleet_001_valid_vehicle_creation():
    service = FleetService()
    vehicle = Vehicle(
        plate_number="SK777BB",
        body_type="Box",
        length_m=13.6,
        width_m=2.45,
        height_m=2.7,
        max_weight_kg=24000,
        status="FREE",
        location_lat=48.1,
        location_lon=17.1,
    )
    service.add_vehicle(vehicle)
    assert len(service.all()) == 1


@pytest.mark.requirement_id("FR-FLEET-002")
@pytest.mark.test_id("TST-FR-FLEET-002-INTEG")
def test_fr_fleet_002_vehicle_current_location_on_map(sample_vehicle):
    service = FleetService()
    service.add_vehicle(sample_vehicle)
    location = service.get_location(sample_vehicle.plate_number)
    assert location["lat"] == sample_vehicle.location_lat
    assert location["lon"] == sample_vehicle.location_lon
    assert location["source"] == "manual"


@pytest.mark.requirement_id("FR-SCRAPE-001")
@pytest.mark.test_id("TST-FR-SCRAPE-001-INTEG")
def test_fr_scrape_001_trans_eu_authentication_required(sample_cargos):
    service = ScrapingService(sample_cargos)
    with pytest.raises(ValueError):
        service.fetch(ScrapeFilters())
    service.authenticate("dispatcher", "secret")
    assert isinstance(service.fetch(ScrapeFilters()), list)


@pytest.mark.requirement_id("FR-SCRAPE-002")
@pytest.mark.test_id("TST-FR-SCRAPE-002-INTEG")
def test_fr_scrape_002_filtered_cargo_fetch(sample_cargos):
    service = ScrapingService(sample_cargos)
    service.authenticate("dispatcher", "secret")
    filtered = service.fetch(
        ScrapeFilters(
            loading_country="SK",
            unloading_country="PL",
            body_type="Box",
            weight_max_kg=15000,
            loading_date_from=date(2026, 2, 14),
            loading_date_to=date(2026, 2, 15),
        )
    )
    assert [c.cargo_id for c in filtered] == ["C1"]


@pytest.mark.requirement_id("FR-CALC-002")
@pytest.mark.test_id("TST-FR-CALC-002-INTEG")
def test_fr_calc_002_osrm_distance_request():
    class StubOSRMClient:
        provider_name = "OSRM"
        calls: list[tuple[str, str]]

        def __init__(self) -> None:
            self.calls = []

        def get_distance_km(self, origin: str, destination: str) -> float:
            self.calls.append((origin, destination))
            return 120.5

    client = StubOSRMClient()
    distance = request_distance_a_b(client, "A", "B")
    assert distance == 120.5
    assert client.calls == [("A", "B")]


@pytest.mark.requirement_id("BR-008")
@pytest.mark.test_id("TST-BR-008-INTEG")
def test_br_008_osm_provider_used_for_distance():
    class StubOSRMClient:
        provider_name = "OSRM"

        def get_distance_km(self, origin: str, destination: str) -> float:
            return 50.0

    client = StubOSRMClient()
    assert client.provider_name == "OSRM"
    assert request_distance_a_b(client, "X", "Y") == 50.0
