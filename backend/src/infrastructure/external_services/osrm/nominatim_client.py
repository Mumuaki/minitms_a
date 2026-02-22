import httpx
import logging
from typing import Optional, Tuple
from backend.src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

class NominatimClient:
    """
    Client for OpenStreetMap Nominatim API (Geocoding).
    """
    BASE_URL = "https://nominatim.openstreetmap.org/search"
    
    # Must identify your application
    USER_AGENT = "MiniTMS/1.0 (internal-testing)"

    async def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Geocodes address to (lat, lon).
        Returns None if not found.
        """
        try:
            headers = {"User-Agent": self.USER_AGENT}
            params = {
                "q": address,
                "format": "json",
                "limit": 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.BASE_URL, params=params, headers=headers, timeout=10.0)
                response.raise_for_status()
                
                data = response.json()
                if not data:
                    logger.warning(f"Nominatim: Address not found: {address}")
                    return None
                
                # Nominatim returns string lat/lon
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                
                logger.info(f"Geocoded '{address}' -> ({lat}, {lon})")
                return lat, lon
                
        except Exception as e:
            logger.error(f"Nominatim Geocoding Error for '{address}': {e}")
            return None
