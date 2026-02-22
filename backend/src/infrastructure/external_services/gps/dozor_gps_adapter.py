"""
GPS Dozor adapter: fetches vehicle list from Dozor API and returns location for a given tracker_id.
Used so fleet cards show the same real location as the GPS tracker page (not mock data).
"""
import os
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

import requests
from backend.src.domain.services.gps_service import GpsService

logger = logging.getLogger(__name__)

GPS_DOZOR_URL = os.getenv("GPS_DOZOR_URL", "https://a1.gpsguard.eu/api/v1/vehicle/")
GPS_DOZOR_USERNAME = os.getenv("GPS_DOZOR_USERNAME", "")
GPS_DOZOR_PASSWORD = os.getenv("GPS_DOZOR_PASSWORD", "")


class DozorGpsAdapter(GpsService):
    """Gets vehicle location from GPS Dozor API (list endpoint). Matches by tracker_id to id or license_plate."""

    def get_vehicle_location(self, tracker_id: str) -> Tuple[Optional[str], Optional[datetime]]:
        if not tracker_id:
            return None, None
        if not GPS_DOZOR_USERNAME or not GPS_DOZOR_PASSWORD:
            logger.info("Dozor: credentials not set (GPS_DOZOR_USERNAME/PASSWORD), skipping")
            return None, None
        try:
            response = requests.get(
                GPS_DOZOR_URL,
                auth=(GPS_DOZOR_USERNAME, GPS_DOZOR_PASSWORD),
                timeout=10,
            )
            if response.status_code != 200:
                logger.warning("Dozor API returned %s", response.status_code)
                return None, None
            data = response.json()
            items = data if isinstance(data, list) else []
            logger.info("Dozor: fetched %d vehicles for match tracker_id=%r", len(items), tracker_id)
        except Exception as e:
            logger.warning("Dozor fetch failed: %s", e)
            return None, None

        def norm(s: str) -> str:
            return (s or "").strip().upper().replace(" ", "").replace("-", "")

        def get_plate(obj: dict) -> str:
            for key in ("license_plate", "plate", "registration", "number_plate", "plate_number", "reg_number", "registration_number"):
                v = obj.get(key)
                if v is not None and str(v).strip():
                    return norm(str(v))
            return ""

        def get_vid(obj: dict) -> str:
            for key in ("id", "vehicle_id", "tracker_id", "imei", "device_id"):
                v = obj.get(key)
                if v is not None and str(v).strip():
                    return norm(str(v))
            return ""

        tracker_id_clean = norm(tracker_id)
        if not tracker_id_clean:
            return None, None
        for item in items:
            vid = get_vid(item)
            plate = get_plate(item)
            if vid == tracker_id_clean or plate == tracker_id_clean:
                logger.info("Dozor: matched tracker_id=%r by %s", tracker_id, "id" if vid == tracker_id_clean else "plate")
                address = (
                    item.get("address")
                    or item.get("location")
                    or item.get("address_formatted")
                    or item.get("position_address")
                    or item.get("formatted_address")
                )
                lat = item.get("lat") or item.get("latitude")
                lon = item.get("lon") or item.get("lng") or item.get("longitude")
                location_str = address
                if not location_str and lat is not None and lon is not None:
                    location_str = f"{lat}, {lon}"
                if not location_str:
                    location_str = item.get("name") or item.get("title") or vid or tracker_id
                last_updated = None
                ts = item.get("last_update") or item.get("updated_at") or item.get("timestamp") or item.get("time")
                if ts:
                    try:
                        last_updated = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                    except Exception:
                        last_updated = datetime.now(timezone.utc)
                else:
                    last_updated = datetime.now(timezone.utc)
                return location_str, last_updated
        logger.info("Dozor: no vehicle matched tracker_id=%r (checked %d items)", tracker_id, len(items))
        return None, None
