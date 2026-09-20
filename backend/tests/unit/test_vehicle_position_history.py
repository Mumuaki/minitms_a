"""
Unit tests for vehicle position history (FR-GPS-004).
"""
from datetime import datetime, timezone

from backend.src.application.use_cases.fleet.refresh_vehicle_location import RefreshVehicleLocationUseCase
from backend.src.infrastructure.external_services.gps.dozor_gps_adapter import _parse_position


def test_extract_country_from_location_string():
    assert RefreshVehicleLocationUseCase._extract_country("DE, 80331, München") == "DE"
    assert RefreshVehicleLocationUseCase._extract_country("PL, 00-001, Warsaw") == "PL"
    assert RefreshVehicleLocationUseCase._extract_country("Munich, DE") is None
    assert RefreshVehicleLocationUseCase._extract_country(None) is None
    assert RefreshVehicleLocationUseCase._extract_country("") is None


def test_parse_position_extracts_structured_fields(monkeypatch):
    monkeypatch.setattr(
        "backend.src.infrastructure.external_services.gps.dozor_gps_adapter._reverse_geocode",
        lambda lat, lon: ("DE", "80331, München"),
    )
    item = {
        "Code": "TRK-1",
        "LastPosition": {"Latitude": "48.13743", "Longitude": "11.57549"},
        "LastPositionTimestamp": "2026-09-21T10:00:00Z",
    }
    pos = _parse_position(item)
    assert pos.latitude == 48.13743
    assert pos.longitude == 11.57549
    assert pos.place_name == "80331, München"
    assert pos.country_code == "DE"
    assert pos.measured_at == datetime(2026, 9, 21, 10, 0, tzinfo=timezone.utc)
