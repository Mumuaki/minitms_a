import pytest

from phase1.auth import AuthService
from phase1.fleet import FleetService
from phase1.models import User
from phase1.profitability import classify_rate, rank_cargos
from phase1.scraping import ScrapeFilters, ScrapingService

@pytest.mark.requirement_id("FR-AUTH-001")
@pytest.mark.requirement_id("FR-FLEET-001")
@pytest.mark.requirement_id("FR-SCRAPE-002")
@pytest.mark.requirement_id("FR-CALC-004")
@pytest.mark.test_id("TST-E2E-PHASE1-DISPATCHER-FLOW-001")
def test_e2e_dispatcher_search_and_rank_flow(sample_vehicle, sample_cargos, now):
    auth = AuthService([User(username="dispatcher", password="secret", role="Dispatcher")])
    session = auth.login("dispatcher", "secret", now)
    assert session.username == "dispatcher"

    fleet = FleetService()
    fleet.add_vehicle(sample_vehicle)
    assert fleet.get_location(sample_vehicle.plate_number) is not None

    scrape = ScrapingService(sample_cargos)
    scrape.authenticate("dispatcher", "secret")
    cargos = scrape.fetch(ScrapeFilters(loading_country="SK", body_type="Box"))
    ranked = rank_cargos(cargos, distance_a_b_km=50.0)
    assert len(ranked) >= 1
    assert ranked[0].gross_rate_per_km >= ranked[-1].gross_rate_per_km


@pytest.mark.requirement_id("FR-AUTH-005")
@pytest.mark.requirement_id("FR-SCRAPE-003")
@pytest.mark.requirement_id("BR-010")
@pytest.mark.requirement_id("BR-013")
@pytest.mark.test_id("TST-E2E-PHASE1-AUDIT-AND-COLOR-001")
def test_e2e_audit_and_profitability_color_flow(sample_cargos, now):
    auth = AuthService([User(username="dispatcher", password="secret", role="Dispatcher")])
    auth.login("dispatcher", "secret", now)
    assert "login_success:dispatcher" in auth.audit_log

    scrape = ScrapingService(sample_cargos)
    assert scrape.validate_refresh_interval(5) is True

    assert classify_rate(0.53).name == "RED"
    assert classify_rate(0.81).name == "GREEN"
