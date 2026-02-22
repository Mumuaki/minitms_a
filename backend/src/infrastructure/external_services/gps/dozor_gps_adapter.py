"""
GPS Dozor adapter: fetches vehicle list from GPS Dozor API and returns location for a given tracker_id.
Used so fleet cards show the same real location as the GPS tracker page (not mock data).
"""
import json
import os
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, List, Any

import requests
from backend.src.domain.services.gps_service import GpsService
from backend.src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

# #region agent log
def _debug_log(msg: str, data: dict, hypothesis_id: str) -> None:
    try:
        path = os.environ.get("DEBUG_LOG_PATH", "/app/debug-fa2d8a.log" if os.path.exists("/app") else "debug-fa2d8a.log")
        payload = {"sessionId": "fa2d8a", "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000), "location": "dozor_gps_adapter", "message": msg, "data": data, "hypothesisId": hypothesis_id}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
# #endregion

def _candidate_urls(base_url: str) -> List[str]:
    """Build a small set of likely Dozor list endpoints."""
    base = (base_url or "").strip() or "https://a1.gpsguard.eu/api/v1/vehicle/"
    normalized = base.rstrip("/")
    candidates = [
        base,
        normalized,
        "https://a1.gpsguard.eu/api/v1/vehicle",
        "https://a1.gpsguard.eu/api/v1/vehicles",
        "https://a1.gpsguard.eu/api/v1/vehicle/list",
    ]
    uniq: List[str] = []
    for url in candidates:
        if url and url not in uniq:
            uniq.append(url)
    return uniq


def _extract_items(data: Any) -> List[dict]:
    """API may return a list or an object like { data: [], vehicles: [], items: [] }."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "vehicles", "items", "results", "list"):
            val = data.get(key)
            if isinstance(val, list):
                return val
    return []


def _get_nested(obj: dict, *keys: str, default: Any = None) -> Any:
    """Get value by nested keys, e.g. _get_nested(item, 'position', 'address', default='')"""
    cur = obj
    for k in keys:
        cur = cur.get(k) if isinstance(cur, dict) else None
        if cur is None:
            return default
    return cur


class DozorGpsAdapter(GpsService):
    """Gets vehicle location from GPS Dozor API. Matches by tracker_id to id or license_plate."""

    @staticmethod
    def is_configured() -> bool:
        return bool(settings.GPS_DOZOR_USERNAME and settings.GPS_DOZOR_PASSWORD)

    def get_vehicle_location(self, tracker_id: str, license_plate: Optional[str] = None, **kwargs: Any) -> Tuple[Optional[str], Optional[datetime]]:
        """Match by tracker_id (e.g. ODOKIRAGEN) or license_plate (e.g. BT152DH)."""
        username = settings.GPS_DOZOR_USERNAME.strip()
        password = settings.GPS_DOZOR_PASSWORD.strip()
        dozor_url = settings.GPS_DOZOR_URL
        # #region agent log
        _debug_log("get_vehicle_location entry", {"tracker_id": tracker_id, "license_plate": license_plate, "is_configured": self.is_configured(), "has_user": bool(username), "has_pass": bool(password)}, "A")
        # #endregion
        search_terms = set()
        if tracker_id:
            search_terms.add((tracker_id or "").strip().upper().replace(" ", "").replace("-", ""))
        if license_plate:
            search_terms.add((license_plate or "").strip().upper().replace(" ", "").replace("-", ""))
        search_terms.discard("")
        if not search_terms:
            return None, None
        if not username or not password:
            logger.info("Dozor: credentials not set (GPS_DOZOR_USERNAME/PASSWORD), skipping")
            return None, None
        items: List[dict] = []
        try:
            status_trace = []
            used_url = None
            for url in _candidate_urls(dozor_url):
                response = requests.get(
                    url,
                    auth=(username, password),
                    timeout=10,
                )
                status_trace.append({"url": url, "status_code": response.status_code})
                if response.status_code != 200:
                    continue
                data = response.json()
                items = _extract_items(data)
                used_url = url
                break
            # #region agent log
            _debug_log("Dozor fetch statuses", {"trace": status_trace}, "B")
            # #endregion
            if not used_url:
                last_code = status_trace[-1]["status_code"] if status_trace else "no-response"
                logger.warning("Dozor API returned only non-200 statuses, last=%s", last_code)
                # #region agent log
                _debug_log("Dozor non-200", {"status_trace": status_trace}, "B")
                # #endregion
                return None, None
            # #region agent log
            first_keys = list(items[0].keys())[:15] if items and isinstance(items[0], dict) else []
            _debug_log("Dozor fetch result", {"used_url": used_url, "items_count": len(items), "first_item_keys": first_keys}, "B")
            # #endregion
            logger.info("Dozor: fetched %d vehicles for match tracker_id=%r plate=%r via %s", len(items), tracker_id, license_plate, used_url)
        except Exception as e:
            logger.warning("Dozor fetch failed: %s", e)
            # #region agent log
            _debug_log("Dozor fetch exception", {"error": str(e)}, "B")
            # #endregion
            return None, None

        def norm(s: str) -> str:
            return (s or "").strip().upper().replace(" ", "").replace("-", "")

        def get_plate(obj: dict) -> str:
            for key in (
                "license_plate", "plate", "registration", "number_plate", "plate_number",
                "reg_number", "registration_number", "label", "number",
            ):
                v = obj.get(key)
                if v is not None and str(v).strip():
                    return norm(str(v))
            return ""

        def get_vid(obj: dict) -> str:
            for key in ("id", "vehicle_id", "tracker_id", "imei", "device_id", "external_id"):
                v = obj.get(key)
                if v is not None and str(v).strip():
                    return norm(str(v))
            return ""

        def get_name(obj: dict) -> str:
            for key in ("name", "title", "label"):
                v = obj.get(key)
                if v is not None and str(v).strip():
                    return norm(str(v))
            return ""

        def matches_any(vid: str, plate: str, name: str) -> bool:
            for term in search_terms:
                if term == vid or term == plate or term == name:
                    return True
                if term in vid or vid in term or term in plate or plate in term or term in name or name in term:
                    return True
            return False

        for item in items:
            if not isinstance(item, dict):
                continue
            vid = get_vid(item)
            plate = get_plate(item)
            name = get_name(item)
            if not matches_any(vid, plate, name):
                continue
            # #region agent log
            _debug_log("Dozor matched", {"vid": vid, "plate": plate, "name": name, "search_terms": list(search_terms)}, "C")
            # #endregion
            logger.info("Dozor: matched tracker_id=%r", tracker_id)
            # Address: top-level and nested (position.address, last_position.address, etc.)
            address = (
                item.get("address")
                or item.get("location")
                or item.get("address_formatted")
                or item.get("position_address")
                or item.get("formatted_address")
                or item.get("last_address")
                or item.get("current_address")
                or item.get("description")
                or _get_nested(item, "position", "address", default="")
                or _get_nested(item, "position", "description", default="")
                or _get_nested(item, "last_position", "address", default="")
                or _get_nested(item, "location", "address", default="")
            )
            if isinstance(address, dict):
                address = address.get("formatted") or address.get("address") or str(address)
            lat = item.get("lat") or item.get("latitude") or _get_nested(item, "position", "lat", default=None)
            lon = item.get("lon") or item.get("lng") or item.get("longitude") or _get_nested(item, "position", "lon", default=None)
            location_str = (address or "").strip() or None
            if not location_str and lat is not None and lon is not None:
                location_str = f"{lat}, {lon}"
            if not location_str:
                location_str = item.get("name") or item.get("title") or (vid or tracker_id)
            ts = item.get("last_update") or item.get("updated_at") or item.get("timestamp") or item.get("time") or _get_nested(item, "position", "timestamp", default=None)
            last_updated = None
            if ts:
                try:
                    last_updated = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                except Exception:
                    last_updated = datetime.now(timezone.utc)
            else:
                last_updated = datetime.now(timezone.utc)
            return location_str, last_updated
        # #region agent log
        _debug_log("Dozor no match", {"tracker_id": tracker_id, "license_plate": license_plate, "items_checked": len(items)}, "C")
        # #endregion
        logger.info("Dozor: no vehicle matched tracker_id=%r plate=%r (checked %d items)", tracker_id, license_plate, len(items))
        return None, None
