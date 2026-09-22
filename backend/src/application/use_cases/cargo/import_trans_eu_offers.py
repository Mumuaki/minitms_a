"""
Import Trans.eu Offers Use Case.
Orchestrates the scraping, normalization, and persistence of cargo offers.
"""
from typing import List, Optional
import logging
import asyncio

from sqlalchemy.orm import Session

from backend.src.domain.repositories.cargo_repository import CargoRepository
from backend.src.infrastructure.external_services.trans_eu.client import TransEuClient
from backend.src.application.dto.cargo_dto import CargoDto, LocationDto, CargoStatusColor
from backend.src.application.use_cases.cargo.calculate_profitability import CalculateProfitabilityUseCase
from backend.src.infrastructure.external_services.osrm.nominatim_client import NominatimClient
from backend.src.infrastructure.external_services.osrm.osrm_client import OSRMClient
from backend.src.domain.services.profitability_service import ProfitabilityService
from backend.src.domain.entities.vehicle_position import VehiclePosition

logger = logging.getLogger(__name__)

GREEN_RATE = 0.85  # максимальная ставка "зелёной" рентабельности (€/км)


def _parse_date(s):
    """22.09, 08:00 - 14:00 -> date(2026, 9, 22)."""
    import re
    from datetime import date as _date
    if not s:
        return None
    nums = re.findall('[0-9]+', s)
    if len(nums) >= 2:
        day, month = int(nums[0]), int(nums[1])
        try:
            return _date(_date.today().year, month, day)
        except ValueError:
            return None
    return None


class ImportTransEuOffersUseCase:

    def __init__(self, cargo_repository: CargoRepository):
        self.cargo_repository = cargo_repository
        self._profitability_calculator = CalculateProfitabilityUseCase()
        self._nominatim = NominatimClient()
        self._osrm = OSRMClient()

    def _get_vehicle_coords(self, db: Optional[Session]):
        """Координаты текущей GPS-точки ТС (для расчёта подачи A→B)."""
        if db is None:
            return None
        try:
            pos = db.query(VehiclePosition).order_by(VehiclePosition.id.desc()).first()
            if pos and pos.latitude is not None and pos.longitude is not None:
                return (float(pos.latitude), float(pos.longitude))
        except Exception:
            pass
        return None

    async def execute(self,
                      loading: str,
                      unloading: Optional[str] = None,
                      loading_radius: int = 75,
                      unloading_radius: int = 75,
                      date_from: str = None,
                      date_to: str = None,
                      unloading_date_from: str = None,
                      unloading_date_to: str = None,
                      weight_to: str = "0.9",
                      length_to: str = None,
                      db: Optional[Session] = None,
                      ) -> List[CargoDto]:
        """Executes the scraping process and saves results to DB."""
        client = await TransEuClient.get_instance()
        try:
            await client.start()
            if not await client.login():
                raise Exception("Failed to login to Trans.eu")

            results_list = await client.search_offers(
                loading_location=loading,
                unloading_location=unloading,
                loading_radius=loading_radius,
                unloading_radius=unloading_radius,
                date_from=date_from,
                date_to=date_to,
                unloading_date_from=unloading_date_from,
                unloading_date_to=unloading_date_to,
                weight_to=weight_to,
                length_to=length_to,
            )

            vehicle_coords = self._get_vehicle_coords(db)
            saved_cargos = []
            if results_list:
                for item in results_list:
                    try:
                        dto = await self._map_dict_to_dto_async(item, vehicle_coords)
                        existing = self.cargo_repository.get_by_external_id(dto.external_id)
                        if existing:
                            dto.id = existing.id
                            saved = self.cargo_repository.update(dto)
                        else:
                            saved = self.cargo_repository.create(dto)
                        saved_cargos.append(saved)
                    except Exception as e:
                        logger.error(f"Failed to save cargo {item.get('external_id')}: {e}")
            return saved_cargos
        except Exception as e:
            logger.error(f"Import failed: {e}")
            raise e
        finally:
            pass

    async def execute_manual(self, timeout_seconds: int = 600, db: Optional[Session] = None) -> List[CargoDto]:
        """Полуавтоматический режим: оператор вручную выполняет поиск, скрапер парсит результат."""
        client = await TransEuClient.get_instance()
        try:
            await client.start()
            if not await client.login():
                raise Exception("Failed to login to Trans.eu")

            results_list = await client.search_offers_manual(timeout_seconds=timeout_seconds)

            vehicle_coords = self._get_vehicle_coords(db)
            saved_cargos = []
            if results_list:
                for item in results_list:
                    try:
                        dto = await self._map_dict_to_dto_async(item, vehicle_coords)
                        existing = self.cargo_repository.get_by_external_id(dto.external_id)
                        if existing:
                            dto.id = existing.id
                            saved = self.cargo_repository.update(dto)
                        else:
                            saved = self.cargo_repository.create(dto)
                        saved_cargos.append(saved)
                    except Exception as e:
                        logger.error(f"Failed to save cargo {item.get('external_id')}: {e}")
            return saved_cargos
        except Exception as e:
            logger.error(f"Manual import failed: {e}")
            raise e
        finally:
            pass

    async def _map_dict_to_dto_async(self, item: dict, vehicle_coords: Optional[tuple] = None) -> CargoDto:
        """Геокодирование + OSRM маршрут (A→B, B→C) + рентабельность."""
        loading_raw = item.get("loading_place", {}).get("raw") or "Unknown"
        unloading_raw = item.get("unloading_place", {}).get("raw") or "Unknown"

        loading_coords = await self._nominatim.get_coordinates(loading_raw)
        await asyncio.sleep(1.0)
        unloading_coords = await self._nominatim.get_coordinates(unloading_raw)
        await asyncio.sleep(1.0)

        loading_lat, loading_lon = loading_coords if loading_coords else (0.0, 0.0)
        unloading_lat, unloading_lon = unloading_coords if unloading_coords else (0.0, 0.0)

        loading_loc = LocationDto(address=loading_raw, country_code="EU", lat=loading_lat, lon=loading_lon)
        unloading_loc = LocationDto(address=unloading_raw, country_code="EU", lat=unloading_lat, lon=unloading_lon)

        # OSRM: A→B (подача) и B→C (перевозка)
        empty_run_km = 0.0
        cargo_run_km = 0.0
        polyline = None

        if vehicle_coords and loading_coords:
            route_a_b = await self._osrm.get_route_info(vehicle_coords[0], vehicle_coords[1], loading_lat, loading_lon)
            if route_a_b:
                empty_run_km, _ = route_a_b

        if loading_coords and unloading_coords:
            route_b_c = await self._osrm.get_route_info(loading_lat, loading_lon, unloading_lat, unloading_lon)
            if route_b_c:
                cargo_run_km, polyline = route_b_c

        price = item.get("price")
        # Цены <= 5 EUR — артефакты парсинга «К обсуждению»: считаем, что цена не заявлена
        effective_price = price if (price and price > 5) else None
        profitability = None
        total_km = empty_run_km + cargo_run_km
        if total_km > 0:
            if effective_price:
                profitability = ProfitabilityService.calculate_profitability(
                    price_eur=effective_price, empty_run_km=empty_run_km, cargo_km=cargo_run_km
                )
            else:
                # нет цены — берём ставку по "зелёной" рентабельности 0.85 €/км
                profitability = ProfitabilityService.calculate_profitability(
                    price_eur=GREEN_RATE * total_km, empty_run_km=empty_run_km, cargo_km=cargo_run_km
                )

        dto = CargoDto(
            id="",
            external_id=(item.get("external_id") or f"gen-{item.get('company_name')}-{item.get('price')}")[:100],
            source="trans.eu",
            loading_place=loading_loc,
            unloading_place=unloading_loc,
            loading_date=_parse_date(item.get("loading_date_raw")),
            unloading_date=_parse_date(item.get("unloading_date_raw")),
            weight=item.get("weight"),
            body_type=(item.get("body_type") or "")[:100] or None,
            description=(item.get("description") or "")[:500] or None,
            price=effective_price,
            distance_trans_eu=item.get("distance_trans_eu"),
            distance_osm=int(cargo_run_km) if cargo_run_km else None,
            profitability=profitability,
            route_polyline=polyline,
            is_hidden=False,
            company_rating=(item.get("company_rating") or "")[:50] or None,
            published_at=(item.get("published_at") or "")[:100] or None,
            created_at=""
        )
        return dto
