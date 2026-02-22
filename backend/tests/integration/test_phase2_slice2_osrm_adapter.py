from unittest.mock import AsyncMock

import pytest

from backend.src.infrastructure.external_services.osrm.adapter import OSRMMapsAdapter


@pytest.mark.requirement_id("FR-CALC-002")
@pytest.mark.test_id("TST-FR-CALC-002-WEB-AT-S2")
@pytest.mark.asyncio
async def test_fr_calc_002_osrm_distance_returns_positive_when_geocoding_ok():
    adapter = OSRMMapsAdapter()
    adapter.nominatim.get_coordinates = AsyncMock(side_effect=[(50.0, 20.0), (52.0, 21.0)])
    adapter.osrm.get_distance = AsyncMock(return_value=123.4)

    distance = await adapter.calculate_distance("Warsaw, PL", "Berlin, DE")

    assert distance == pytest.approx(123.4)


@pytest.mark.requirement_id("FR-CALC-002")
@pytest.mark.test_id("TST-FR-CALC-002-WEB-INTEG-S2")
@pytest.mark.asyncio
async def test_fr_calc_002_osrm_distance_returns_zero_when_origin_not_geocoded():
    adapter = OSRMMapsAdapter()
    adapter.nominatim.get_coordinates = AsyncMock(return_value=None)

    distance = await adapter.calculate_distance("UNKNOWN", "Berlin, DE")

    assert distance == pytest.approx(0.0)
