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
from datetime import datetime, timezone
from typing import Optional, Tuple

import requests

from backend.src.domain.services.gps_service import GpsService
from backend.src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

_NOMINATIM_UA = "MiniTMS/1.0 (fleet-tracker)"


def _base_url() -> str:
    url = settings.GPS_DOZOR_URL.rstrip("/")
    # Allow both full list-url and base-url in settings
    for suffix in ("/vehicle", "/vehicles", "/vehicle/", "/vehicles/"):
        if url.endswith(suffix.rstrip("/")):
            url = url[: url.rfind("/")]
    return url  # e.g. https://a1.gpsguard.eu/api/v1


def _creds() -> Tuple[str, str]:
    return settings.GPS_DOZOR_USERNAME.strip(), settings.GPS_DOZOR_PASSWORD.strip()


def _reverse_geocode(lat: str, lon: str) -> Optional[str]:
    """Free Nominatim reverse geocoding. Returns formatted address: ISO-2, postal code, name of location."""
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
            iso = address.get("country_code", "").upper()
            postcode = address.get("postcode", "")
            
            city = (address.get("city") or 
                    address.get("town") or 
                    address.get("village") or 
                    address.get("municipality") or 
                    address.get("county") or 
                    "")
            
            parts = [p for p in [iso, postcode, city] if p]
            if parts:
                return ", ".join(parts)
                
            return data.get("display_name") or None
    except Exception as e:
        logger.debug("Nominatim reverse geocode failed: %s", e)
    return None


def _parse_vehicle(item: dict) -> Tuple[Optional[str], Optional[datetime]]:
    """Extract (location_str, last_updated) from a GPS Guard vehicle object."""
    pos = item.get("LastPosition") or {}
    lat = pos.get("Latitude")
    lon = pos.get("Longitude")

    address = None
    if lat and lon:
        address = _reverse_geocode(str(lat), str(lon))
    location_str = address or (f"{lat}, {lon}" if lat and lon else None)

    ts = item.get("LastPositionTimestamp")
    last_updated: Optional[datetime] = None
    if ts:
        try:
            last_updated = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except Exception:
            last_updated = datetime.now(timezone.utc)
    else:
        last_updated = datetime.now(timezone.utc)

    return location_str, last_updated


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

    def get_vehicle_location(
        self,
        tracker_id: str,
        license_plate: Optional[str] = None,
        **kwargs,
    ) -> Tuple[Optional[str], Optional[datetime]]:
        """
        Match vehicle by tracker_id (= GPS Guard Code, e.g. ODOKIRAGEN)
        or license_plate (= GPS Guard Name, e.g. BT152DH).
        """
        if not self.is_configured():
            logger.info("GPS Guard: credentials not configured")
            return None, None

        norm = lambda s: (s or "").strip().upper().replace(" ", "").replace("-", "")
        search = {norm(tracker_id), norm(license_plate)} - {""}

        # --- Fast path: try direct vehicle fetch by tracker_id as Code ---
        if tracker_id:
            item = self._get_vehicle_direct(tracker_id.strip())
            if item:
                loc, ts = _parse_vehicle(item)
                logger.info("GPS Guard: matched via direct fetch Code=%r → %s", tracker_id, loc)
                return loc, ts

        # --- Fallback: scan all vehicles across all groups ---
        groups = self._get_groups()
        if not groups:
            logger.warning("GPS Guard: no groups returned (bad credentials or empty account)")
            return None, None

        for group in groups:
            group_code = group.get("Code", "")
            vehicles = self._get_vehicles_in_group(group_code)
            for item in vehicles:
                code_norm = norm(item.get("Code", ""))
                name_norm = norm(item.get("Name", ""))
                spz_norm = norm(item.get("SPZ", "") or "")
                if search & {code_norm, name_norm, spz_norm}:
                    loc, ts = _parse_vehicle(item)
                    logger.info(
                        "GPS Guard: matched Code=%r Name=%r in group %s → %s",
                        item.get("Code"), item.get("Name"), group_code, loc,
                    )
                    return loc, ts

        logger.info(
            "GPS Guard: no match for tracker_id=%r plate=%r in %d group(s)",
            tracker_id, license_plate, len(groups),
        )
        return None, None
