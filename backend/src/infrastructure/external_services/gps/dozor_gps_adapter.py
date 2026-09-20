"""
GPS Guard / GPS Dozor adapter.

Correct API flow (https://a1.gpsguard.eu):
  GET /api/v1/groups                        → list of groups [{Code, Name}]
  GET /api/v1/vehicles/group/{group_code}   → vehicles in group
  GET /api/v1/vehicle/{vehicle_code}        → single vehicle (fast path)

Vehicle object fields used:
  Code               — matches gps_tracker_id stored in our DB
  Name               — usually the license plate
  LastPosition       — {Latitude, Longitude}  (strings)
  LastPositionTimestamp — ISO-8601 UTC
  Speed, Odometer, BatteryPercentage, IsActive
"""
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple

import requests

from backend.src.domain.services.gps_service import GpsService
from backend.src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

_NOMINATIM_UA = "MiniTMS/1.0 (fleet-tracker)"


@dataclass
class GpsPosition:
    """Структурированная GPS-позиция ТС (FR-GPS-004)."""

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_name: Optional[str] = None
    country_code: Optional[str] = None
    measured_at: Optional[datetime] = None


def _base_url() -> str:
    url = settings.GPS_DOZOR_URL.rstrip("/")
    # Allow both full list-url and base-url in settings
    for suffix in ("/vehicle", "/vehicles", "/vehicle/", "/vehicles/"):
        if url.endswith(suffix.rstrip("/")):
            url = url[: url.rfind("/")]
    return url  # e.g. https://a1.gpsguard.eu/api/v1


def _creds() -> Tuple[str, str]:
    return settings.GPS_DOZOR_USERNAME.strip(), settings.GPS_DOZOR_PASSWORD.strip()


def _reverse_geocode(lat: str, lon: str) -> Tuple[Optional[str], Optional[str]]:
    """Обратное геокодирование через Nominatim. Возвращает (country_code, place_name)."""
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json", "addressdetails": "1"},
            headers={"User-Agent": _NOMINATIM_UA},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            address = data.get("address", {})
            iso = address.get("country_code", "").upper() or None
            postcode = address.get("postcode", "")

            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
                or address.get("county")
                or ""
            )

            place = ", ".join([p for p in [postcode, city] if p]) or None
            if iso or place:
                return iso, place
            return None, data.get("display_name")
    except Exception as e:
        logger.debug("Nominatim reverse geocode failed: %s", e)
    return None, None


def _parse_position(item: dict) -> GpsPosition:
    """Извлекает структурированную позицию (lat/lon/place/country/measured_at)."""
    pos = item.get("LastPosition") or {}
    lat_s = pos.get("Latitude")
    lon_s = pos.get("Longitude")

    lat: Optional[float] = None
    lon: Optional[float] = None
    try:
        lat = float(lat_s) if lat_s is not None else None
        lon = float(lon_s) if lon_s is not None else None
    except (ValueError, TypeError):
        lat = lon = None

    country: Optional[str] = None
    place: Optional[str] = None
    if lat is not None and lon is not None:
        country, place = _reverse_geocode(str(lat), str(lon))
    if not place:
        place = f"{lat}, {lon}" if (lat is not None and lon is not None) else None

    ts = item.get("LastPositionTimestamp")
    measured: Optional[datetime] = None
    if ts:
        try:
            measured = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except Exception:
            measured = datetime.now(timezone.utc)
    else:
        measured = datetime.now(timezone.utc)

    return GpsPosition(
        latitude=lat,
        longitude=lon,
        place_name=place,
        country_code=country,
        measured_at=measured,
    )


def _parse_vehicle(item: dict) -> Tuple[Optional[str], Optional[datetime]]:
    """Обратная совместимость: возвращает (location_str, last_updated)."""
    pos = _parse_position(item)
    return pos.place_name, pos.measured_at


class DozorGpsAdapter(GpsService):
    """Gets vehicle location from GPS Guard API (a1.gpsguard.eu)."""

    @staticmethod
    def is_configured() -> bool:
        u, p = _creds()
        return bool(u and p)

    def _get_groups(self) -> list:
        u, p = _creds()
        try:
            r = requests.get(
                f"{_base_url()}/groups",
                auth=(u, p),
                timeout=10,
            )
            if r.status_code == 200:
                return r.json() if isinstance(r.json(), list) else []
            logger.warning("GPS Guard /groups returned HTTP %s", r.status_code)
        except Exception as e:
            logger.warning("GPS Guard /groups failed: %s", e)
        return []

    def _get_vehicles_in_group(self, group_code: str) -> list:
        u, p = _creds()
        try:
            r = requests.get(
                f"{_base_url()}/vehicles/group/{group_code}",
                auth=(u, p),
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                return data if isinstance(data, list) else []
            logger.warning("GPS Guard /vehicles/group/%s returned HTTP %s", group_code, r.status_code)
        except Exception as e:
            logger.warning("GPS Guard /vehicles/group/%s failed: %s", group_code, e)
        return []

    def _get_vehicle_direct(self, code: str) -> Optional[dict]:
        """Fast path: fetch single vehicle by its GPS Guard code."""
        u, p = _creds()
        try:
            r = requests.get(
                f"{_base_url()}/vehicle/{code}",
                auth=(u, p),
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                return data if isinstance(data, dict) else None
        except Exception as e:
            logger.debug("GPS Guard /vehicle/%s failed: %s", code, e)
        return None

    def _find_vehicle_item(
        self,
        tracker_id: str,
        license_plate: Optional[str] = None,
    ) -> Optional[dict]:
        """Ищет объект ТС по tracker_id (= Code) или license_plate (= Name/SPZ)."""
        norm = lambda s: (s or "").strip().upper().replace(" ", "").replace("-", "")
        search = {norm(tracker_id), norm(license_plate)} - {""}

        # --- Fast path: direct vehicle fetch by tracker_id as Code ---
        if tracker_id:
            item = self._get_vehicle_direct(tracker_id.strip())
            if item:
                logger.info("GPS Guard: matched via direct fetch Code=%r", tracker_id)
                return item

        # --- Fallback: scan all vehicles across all groups ---
        groups = self._get_groups()
        if not groups:
            logger.warning("GPS Guard: no groups returned (bad credentials or empty account)")
            return None

        for group in groups:
            group_code = group.get("Code", "")
            vehicles = self._get_vehicles_in_group(group_code)
            for item in vehicles:
                code_norm = norm(item.get("Code", ""))
                name_norm = norm(item.get("Name", ""))
                spz_norm = norm(item.get("SPZ", "") or "")
                if search & {code_norm, name_norm, spz_norm}:
                    logger.info(
                        "GPS Guard: matched Code=%r Name=%r in group %s",
                        item.get("Code"), item.get("Name"), group_code,
                    )
                    return item

        logger.info(
            "GPS Guard: no match for tracker_id=%r plate=%r in %d group(s)",
            tracker_id, license_plate, len(groups),
        )
        return None

    def get_vehicle_location(
        self,
        tracker_id: str,
        license_plate: Optional[str] = None,
        **kwargs,
    ) -> Tuple[Optional[str], Optional[datetime]]:
        """Возвращает (location_str, last_updated) — для обратной совместимости."""
        if not self.is_configured():
            logger.info("GPS Guard: credentials not configured")
            return None, None
        item = self._find_vehicle_item(tracker_id, license_plate)
        if item is None:
            return None, None
        return _parse_vehicle(item)

    def get_vehicle_position(
        self,
        tracker_id: str,
        license_plate: Optional[str] = None,
        **kwargs,
    ) -> Optional[GpsPosition]:
        """Возвращает структурированную GPS-позицию ТС (FR-GPS-004)."""
        if not self.is_configured():
            return None
        item = self._find_vehicle_item(tracker_id, license_plate)
        if item is None:
            return None
        return _parse_position(item)
