import pytest

from phase1.fleet import FleetService
from phase1.scraping import ScrapingService

@pytest.mark.requirement_id("FR-FLEET-003")
@pytest.mark.test_id("TST-FR-FLEET-003-UNIT")
def test_fr_fleet_003_vehicle_status_enum():
    statuses = FleetService().allowed_statuses()
    assert statuses == {"FREE", "IN_TRIP", "MAINTENANCE", "UNAVAILABLE"}


@pytest.mark.requirement_id("FR-SCRAPE-003")
@pytest.mark.test_id("TST-FR-SCRAPE-003-UNIT")
def test_fr_scrape_003_refresh_interval_min_five_minutes(sample_cargos):
    service = ScrapingService(sample_cargos)
    assert service.validate_refresh_interval(5) is True
    assert service.validate_refresh_interval(4) is False
