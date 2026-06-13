import requests
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple
from backend.src.domain.services.gps_service import GpsService
from backend.src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

class GpsGuardAdapter(GpsService):
    def _reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """
        Использует публичный API Nominatim (OpenStreetMap) для получения города и страны по координатам.
        Соблюдает ограничение 1 запрос/сек и передает User-Agent.
        """
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        headers = {
            "User-Agent": "MiniTMS-GPS-Adapter/1.0 (contact@minitms.local)"
        }
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                address = data.get("address", {})
                
                # Приоритет полей для города
                city = address.get("city") or address.get("town") or address.get("village")
                country = address.get("country_code", "").upper()
                
                if city and country:
                    return f"{city}, {country}"
                elif city:
                    return city
                elif country:
                    return country
        except Exception as e:
            logger.warning(f"Nominatim Geocoding error: {e}")
            
        return None

    def get_vehicle_location(self, tracker_id: str) -> Tuple[Optional[str], Optional[datetime]]:
        """
        Fetches vehicle location from https://a1.gpsguard.eu/api/v1/vehicle/{tracker_id}
        """
        url = f"{settings.GPS_GUARD_BASE_URL}/vehicle/{tracker_id}"
        headers = {}
        if settings.GPS_GUARD_API_KEY:
            headers["Authorization"] = f"Bearer {settings.GPS_GUARD_API_KEY}"

        try:
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                lat = data.get("lat") or data.get("latitude")
                lon = data.get("lon") or data.get("lng") or data.get("longitude")
                address = data.get("address")
                
                last_updated_str = data.get("last_updated") or data.get("timestamp") or data.get("time")
                last_updated = None
                
                if last_updated_str:
                    try:
                        last_updated = datetime.fromisoformat(str(last_updated_str).replace('Z', '+00:00'))
                    except Exception:
                        last_updated = datetime.now(timezone.utc)
                else:
                    last_updated = datetime.now(timezone.utc)

                location_str = None
                if address and isinstance(address, dict):
                    iso = address.get("country_code", "").upper()
                    postcode = address.get("postcode", "")
                    city = address.get("city") or address.get("town") or ""
                    parts = [p for p in [iso, postcode, city] if p]
                    if parts:
                        location_str = ", ".join(parts)
                elif isinstance(address, str):
                    location_str = address

                # Обратное геокодирование, если от провайдера нет адреса, но есть координаты
                if not location_str and lat and lon:
                    try:
                        location_str = self._reverse_geocode(float(lat), float(lon))
                    except ValueError:
                        pass
                        
                    # Fallback на raw координаты
                    if not location_str:
                        location_str = f"{lat}, {lon}"
                        
                return location_str, last_updated
            else:
                logger.warning(f"GPS Guard API Error: {response.status_code} - {response.text}")
                return None, None
                
        except Exception as e:
            logger.error(f"GPS Guard Connection Error: {e}")
            return None, None
