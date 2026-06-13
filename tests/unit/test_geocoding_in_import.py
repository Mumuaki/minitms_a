"""
Unit test: Geocoding integration in ImportTransEuOffersUseCase.

Проверяем, что _map_dict_to_dto_async:
1. Вызывает NominatimClient.get_coordinates с правильными адресами
2. При get_coordinates → None координаты остаются 0.0, 0.0
3. При get_coordinates → (48.13, 11.58) координаты попадают в LocationDto
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.src.application.use_cases.cargo.import_trans_eu_offers import ImportTransEuOffersUseCase


@pytest.fixture
def use_case():
    """Создаём экземпляр UseCase с замоканным репозиторием."""
    mock_repo = MagicMock()
    uc = ImportTransEuOffersUseCase(cargo_repository=mock_repo)
    return uc


@pytest.fixture
def sample_item():
    """Пример данных от маппера Trans.eu."""
    return {
        "external_id": "test-123",
        "loading_place": {"raw": "DE 80997 München"},
        "unloading_place": {"raw": "PL 00-001 Warszawa"},
        "weight": 18.5,
        "body_type": "Tent",
        "price": 1200.0,
        "distance_trans_eu": 850,
        "company_name": "TestCompany",
    }


@pytest.mark.asyncio
async def test_geocoding_with_coordinates(use_case, sample_item):
    """
    Когда Nominatim возвращает координаты,
    они должны попасть в LocationDto.
    """
    use_case._nominatim.get_coordinates = AsyncMock(side_effect=[
        (48.13, 11.58),   # München
        (52.23, 21.01),   # Warszawa
    ])

    dto = await use_case._map_dict_to_dto_async(sample_item)

    # Проверяем вызовы
    assert use_case._nominatim.get_coordinates.call_count == 2
    use_case._nominatim.get_coordinates.assert_any_call("DE 80997 München")
    use_case._nominatim.get_coordinates.assert_any_call("PL 00-001 Warszawa")

    # Проверяем координаты
    assert dto.loading_place.lat == 48.13
    assert dto.loading_place.lon == 11.58
    assert dto.unloading_place.lat == 52.23
    assert dto.unloading_place.lon == 21.01

    # Проверяем адреса
    assert dto.loading_place.address == "DE 80997 München"
    assert dto.unloading_place.address == "PL 00-001 Warszawa"


@pytest.mark.asyncio
async def test_geocoding_fallback_on_none(use_case, sample_item):
    """
    Когда Nominatim возвращает None,
    координаты должны остаться 0.0, 0.0.
    """
    use_case._nominatim.get_coordinates = AsyncMock(return_value=None)

    dto = await use_case._map_dict_to_dto_async(sample_item)

    assert dto.loading_place.lat == 0.0
    assert dto.loading_place.lon == 0.0
    assert dto.unloading_place.lat == 0.0
    assert dto.unloading_place.lon == 0.0


@pytest.mark.asyncio
async def test_geocoding_partial_failure(use_case, sample_item):
    """
    Когда loading геокодируется, а unloading — нет.
    """
    use_case._nominatim.get_coordinates = AsyncMock(side_effect=[
        (48.13, 11.58),  # loading — OK
        None,            # unloading — fail
    ])

    dto = await use_case._map_dict_to_dto_async(sample_item)

    assert dto.loading_place.lat == 48.13
    assert dto.loading_place.lon == 11.58
    assert dto.unloading_place.lat == 0.0
    assert dto.unloading_place.lon == 0.0


@pytest.mark.asyncio
async def test_dto_fields_preserved(use_case, sample_item):
    """
    Остальные поля DTO заполняются из item корректно.
    """
    use_case._nominatim.get_coordinates = AsyncMock(return_value=None)

    dto = await use_case._map_dict_to_dto_async(sample_item)

    assert dto.external_id == "test-123"
    assert dto.source == "trans.eu"
    assert dto.weight == 18.5
    assert dto.body_type == "Tent"
    assert dto.price == 1200.0
    assert dto.distance_trans_eu == 850
    assert dto.is_hidden is False
