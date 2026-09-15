"""
GpsServiceImpl — конкретная реализация доменного сервиса GpsService.

Выбор провайдера:
  * DozorGpsAdapter (GPS Guard, https://a1.gpsguard.eu) — если в .env заданы
    GPS_DOZOR_USERNAME / GPS_DOZOR_PASSWORD;
  * MockGpsService — если креды не заданы (детерминированные демо-локации).

Модуль отсутствовал в репозитории, из-за чего падали celery-worker,
celery-beat и scraping-worker с ModuleNotFoundError.
"""

import logging
from datetime import datetime
from typing import Optional, Tuple

from backend.src.domain.services.gps_service import GpsService
from backend.src.infrastructure.external_services.gps.dozor_gps_adapter import DozorGpsAdapter
from backend.src.infrastructure.external_services.gps.mock_gps_service import MockGpsService

logger = logging.getLogger(__name__)


class GpsServiceImpl(GpsService):
    """Единая точка доступа к GPS: реальный провайдер с мок-фолбэком."""

    def __init__(self) -> None:
        if DozorGpsAdapter.is_configured():
            self._delegate: GpsService = DozorGpsAdapter()
            logger.info("GpsServiceImpl: используем DozorGpsAdapter (GPS Guard)")
        else:
            self._delegate = MockGpsService()
            logger.warning(
                "GpsServiceImpl: GPS_DOZOR_* не заданы — используем MockGpsService"
            )

    def get_vehicle_location(
        self,
        tracker_id: str,
        license_plate: Optional[str] = None,
        **kwargs,
    ) -> Tuple[Optional[str], Optional[datetime]]:
        """Делегирует запрос выбранному провайдеру."""
        if isinstance(self._delegate, MockGpsService):
            # MockGpsService принимает только tracker_id
            return self._delegate.get_vehicle_location(tracker_id)

        return self._delegate.get_vehicle_location(
            tracker_id, license_plate=license_plate, **kwargs
        )
