import logging
from typing import List, Optional
from datetime import datetime

from backend.src.application.ports.scraping_port import TransEuScraperPort
from backend.src.domain.repositories.vehicle_repository import VehicleRepository
from backend.src.application.dto.cargo_dto import SearchCargoRequestDto

logger = logging.getLogger(__name__)

class SearchCargoByVehicleUseCase:
    """
    Use Case для поиска грузов по транспортному средству.
    (UC-CARGO-01)
    """
    def __init__(self, vehicle_repo: VehicleRepository, scraper_port: TransEuScraperPort):
        self._vehicle_repo = vehicle_repo
        self._scraper_port = scraper_port

    async def execute(
        self, 
        vehicle_id: str, 
        unloading: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        unloading_date_from: Optional[str] = None,
        unloading_date_to: Optional[str] = None,
        loading_radius: int = 75,
        unloading_radius: int = 75,
    ) -> List[dict]:
        """
        Выполняет поиск грузов, используя текущее местоположение ТС 
        и его характеристики (грузоподъемность, длина).
        """
        # 1. Получаем ТС
        vehicle = self._vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle with id {vehicle_id} not found")

        # 2. Проверяем локацию
        if not getattr(vehicle, "current_location", None):
            raise ValueError(f"Vehicle {vehicle_id} has no current_location. Cannot search.")

        loading = vehicle.current_location

        # 3. Достаем параметры ТС
        # Если есть payload_capacity - используем его
        weight_to = str(getattr(vehicle, "payload_capacity", 0.9))
        
        # Длина кузова. По умолчанию для Trans.eu часто нужно передавать в "погрузочных метрах",
        # но если это сырая длина (м), передаем её как строку
        length = getattr(vehicle, "length", None)
        length_to = str(length) if length is not None else None

        logger.info(f"Searching cargos for vehicle {vehicle_id} from {loading}")
        
        criteria = {
            "loading_location": loading,
            "unloading_location": unloading,
            "loading_radius": loading_radius,
            "unloading_radius": unloading_radius,
            "date_from": date_from,
            "date_to": date_to,
            "unloading_date_from": unloading_date_from,
            "unloading_date_to": unloading_date_to,
            "weight_to": weight_to,
            "length_to": length_to
        }
        
        # 4. Вызов порта скрапера
        # Сначала логинимся (согласно контракту порта)
        await self._scraper_port.login()
        results = await self._scraper_port.fetch_offers(criteria)
        
        return results
