"""Refresh vehicle current_location from GPS (Dozor first, then Guard, then mock)."""
import logging
from typing import Optional
from sqlalchemy.orm import Session

from backend.src.application.dto.vehicle_dto import VehicleResponse
from backend.src.domain.entities.vehicle_position import VehiclePosition
from backend.src.infrastructure.persistence.sqlalchemy.repositories.vehicle_repository_impl import VehicleRepositoryImpl
from backend.src.infrastructure.external_services.gps.dozor_gps_adapter import DozorGpsAdapter, GpsPosition
from backend.src.infrastructure.external_services.gps.gps_guard_adapter import GpsGuardAdapter
from backend.src.infrastructure.external_services.gps.mock_gps_service import MockGpsService

logger = logging.getLogger(__name__)


class RefreshVehicleLocationUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.repository = VehicleRepositoryImpl(db)
        self.dozor_gps = DozorGpsAdapter()
        self.gps_guard = GpsGuardAdapter()
        self.mock_gps = MockGpsService()

    @staticmethod
    def _extract_country(loc: Optional[str]) -> Optional[str]:
        """Best-effort ISO-2 country from a 'ISO-2, ...' location string."""
        if not loc:
            return None
        first = loc.split(",")[0].strip()
        if len(first) == 2 and first.isalpha():
            return first.upper()
        return None

    def _record_position(
        self,
        vehicle_id: int,
        loc: Optional[str],
        measured_at,
        position: Optional[GpsPosition] = None,
    ) -> None:
        """Сохраняет запись в историю перемещений ТС (FR-GPS-004)."""
        if not loc and position is None:
            return
        try:
            if position is not None:
                self.db.add(VehiclePosition(
                    vehicle_id=vehicle_id,
                    latitude=position.latitude,
                    longitude=position.longitude,
                    place_name=position.place_name,
                    country_code=position.country_code,
                    measured_at=position.measured_at,
                ))
            else:
                self.db.add(VehiclePosition(
                    vehicle_id=vehicle_id,
                    latitude=None,
                    longitude=None,
                    place_name=loc,
                    country_code=self._extract_country(loc),
                    measured_at=measured_at,
                ))
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.warning("Failed to record vehicle position history", exc_info=True)

    def execute(self, vehicle_id: int) -> Optional[VehicleResponse]:
        vehicle = self.repository.get_by_id(vehicle_id)
        if not vehicle:
            return None
        if not vehicle.gps_tracker_id:
            return VehicleResponse.model_validate(vehicle)

        loc = None
        last_updated = None
        position: Optional[GpsPosition] = None

        # 1) Dozor primary — structured position (lat/lon/place/country)
        if self.dozor_gps.is_configured():
            position = self.dozor_gps.get_vehicle_position(
                vehicle.gps_tracker_id, license_plate=vehicle.license_plate
            )
            if position is not None and position.place_name:
                loc = position.place_name
                if position.country_code:
                    loc = f"{position.country_code}, {position.place_name}"
                last_updated = position.measured_at

        # 2) Guard fallback
        if loc is None:
            loc, last_updated = self.gps_guard.get_vehicle_location(vehicle.gps_tracker_id)

        # 3) Mock fallback (only when Dozor is not configured)
        if loc is None and not self.dozor_gps.is_configured():
            loc, last_updated = self.mock_gps.get_vehicle_location(vehicle.gps_tracker_id)

        vehicle.current_location = loc
        vehicle.gps_last_updated = last_updated
        updated = self.repository.save(vehicle)

        self._record_position(
            vehicle_id=vehicle_id,
            loc=loc,
            measured_at=last_updated,
            position=position,
        )

        return VehicleResponse.model_validate(updated)
