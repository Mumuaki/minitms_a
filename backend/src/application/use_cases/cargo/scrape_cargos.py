"""
Use Case: ScrapeCargoUseCase
Осуществляет парсинг грузов по заданному ТС (UC-CARGO-01).
"""
import logging
from typing import List, Optional
from datetime import datetime
import asyncio

from backend.src.application.ports.scraping_port import TransEuScraperPort
from backend.src.domain.services.gps_service import GpsService
from backend.src.domain.repositories.vehicle_repository import VehicleRepository
from backend.src.domain.repositories.cargo_repository import CargoRepository
from backend.src.application.dto.cargo_dto import CargoDto, LocationDto
from backend.src.infrastructure.external_services.osrm.nominatim_client import NominatimClient
from backend.src.infrastructure.external_services.osrm.osrm_client import OSRMClient
from backend.src.domain.services.profitability_service import ProfitabilityService

logger = logging.getLogger(__name__)

class ScrapeCargoUseCase:
    """
    Бизнес-логика для запуска скрапинга грузов, привязанного к конкретному ТС.
    """
    def __init__(
        self,
        vehicle_repository: VehicleRepository,
        gps_service: GpsService,
        scraper_port: TransEuScraperPort,
        cargo_repository: CargoRepository
    ):
        self._vehicle_repo = vehicle_repository
        self._gps_service = gps_service
        self._scraper_port = scraper_port
        self._cargo_repo = cargo_repository
        self._nominatim = NominatimClient()
        self._osrm = OSRMClient()

    async def execute(self, vehicle_id: str, radius: int = 75, **filters) -> List[CargoDto]:
        """
        Запуск поиска грузов для конкретного ТС.
        """
        # 1. Получаем ТС
        vehicle = self._vehicle_repo.get_by_id(int(vehicle_id) if vehicle_id.isdigit() else 0)
        if not vehicle:
            # Если ТС нет в репозитории, для демо-целей можем пропустить строгую валидацию,
            # но в реальном проде это ошибка.
            pass
            
        # 2. Получаем позицию ТС из GPS
        location_str, last_update = self._gps_service.get_vehicle_location(vehicle_id)
        if not location_str:
            raise ValueError(f"Could not retrieve GPS location for vehicle {vehicle_id}")

        logger.info(f"Vehicle {vehicle_id} location is {location_str}. Starting scraping...")
        vehicle_coords = await self._nominatim.get_coordinates(location_str)

        # 3. Аутентификация в скрапере
        is_logged_in = await self._scraper_port.login()
        if not is_logged_in:
            raise Exception("Failed to login to Trans.eu")

        # 4. Формируем критерии поиска
        # Если vehicle.load_capacity задано, можно передать weight_to, но фильтры могут переопределить.
        weight_to = filters.get("weight_to", str(vehicle.load_capacity) if vehicle and vehicle.load_capacity else "0.9")
        
        criteria = {
            "loading_location": location_str,
            "loading_radius": radius,
            "unloading_radius": filters.get("unloading_radius", 75),
            "date_from": filters.get("date_from"),
            "date_to": filters.get("date_to"),
            "unloading_date_from": filters.get("unloading_date_from"),
            "unloading_date_to": filters.get("unloading_date_to"),
            "weight_to": weight_to,
            "length_to": filters.get("length_to")
        }

        # 5. Парсинг
        try:
            results_list = await self._scraper_port.fetch_offers(criteria)
        except Exception as e:
            logger.error(f"Scraping failed after retries: {e}. Falling back to stale data.")
            from backend.src.application.dto.cargo_dto import SearchCargoRequestDto
            search_request = SearchCargoRequestDto(
                vehicle_body_type=vehicle.body_type if vehicle else None,
                vehicle_max_weight=vehicle.max_weight if vehicle else None,
                limit=50
            )
            fallback_response = self._cargo_repo.search_cargos(search_request)
            for cargo in fallback_response.items:
                cargo.is_stale = True
            return fallback_response.items

        # Окно идемпотентности: округление до начала текущего часа
        now = datetime.utcnow()
        snapshot_time_bucket = now.replace(minute=0, second=0, microsecond=0)

        # 6. Нормализация и сохранение
        saved_cargos = []
        if results_list:
            for item in results_list:
                try:
                    dto = await self._map_dict_to_dto_async(item, vehicle_coords)
                    saved = self._cargo_repo.upsert(dto, snapshot_time_bucket)
                    saved_cargos.append(saved)
                except Exception as e:
                    logger.error(f"Failed to save cargo {item.get('external_id')}: {e}")

        return saved_cargos

    async def _map_dict_to_dto_async(self, item: dict, vehicle_coords: Optional[tuple]) -> CargoDto:
        """Геокодирование и преобразование сырого словаря в CargoDto."""
        loading_raw = item.get("loading_place", {}).get("raw") or "Unknown"
        unloading_raw = item.get("unloading_place", {}).get("raw") or "Unknown"

        loading_coords = await self._nominatim.get_coordinates(loading_raw)
        await asyncio.sleep(1.0) # Rate limiting Nominatim
        unloading_coords = await self._nominatim.get_coordinates(unloading_raw)
        await asyncio.sleep(1.0)

        loading_lat, loading_lon = loading_coords if loading_coords else (0.0, 0.0)
        unloading_lat, unloading_lon = unloading_coords if unloading_coords else (0.0, 0.0)

        loading_loc = LocationDto(
            address=loading_raw,
            country_code="EU",
            lat=loading_lat,
            lon=loading_lon
        )
        unloading_loc = LocationDto(
            address=unloading_raw,
            country_code="EU",
            lat=unloading_lat,
            lon=unloading_lon
        )

        # OSRM routing
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
        profitability = None
        if price and price > 0:
            profitability = ProfitabilityService.calculate_profitability(
                price_eur=price,
                empty_run_km=empty_run_km,
                cargo_km=cargo_run_km
            )

        dto = CargoDto(
            id="",
            external_id=item.get("external_id") or f"gen-{item.get('company_name')}-{item.get('price')}",
            source="trans.eu",
            loading_place=loading_loc,
            unloading_place=unloading_loc,
            loading_date=None,
            unloading_date=None,
            weight=item.get("weight"),
            body_type=item.get("body_type"),
            price=price,
            distance_trans_eu=item.get("distance_trans_eu"),
            distance_osm=int(cargo_run_km) if cargo_run_km else None,
            profitability=profitability,
            route_polyline=polyline,
            is_hidden=False,
            company_rating=item.get("company_rating"),
            published_at=item.get("published_at"),
            created_at=""
        )
        return dto
