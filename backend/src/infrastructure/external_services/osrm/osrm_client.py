import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class OSRMClient:
    """
    Client for OSRM (Open Source Routing Machine).
    Uses public demo server by default (router.project-osrm.org).
    """
    # Demo server limits: 1 request/s approx.
    BASE_URL = "http://router.project-osrm.org/route/v1/driving"

    async def get_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[float]:
        """
        Calculates driving distance in kilometers.
        """
        try:
            # Format: {lon},{lat};{lon},{lat}  (Note: OSRM uses lon,lat)
            coords = f"{lon1},{lat1};{lon2},{lat2}"
            url = f"{self.BASE_URL}/{coords}"
            
            params = {
                "overview": "false",
                "steps": "false"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("code") != "Ok" or not data.get("routes"):
                    logger.error(f"OSRM Error: {data.get('code')}")
                    return None
                
                # Distance in meters
                meters = data["routes"][0]["distance"]
                km = meters / 1000.0
                
                return round(km, 2)
                
        except Exception as e:
            logger.error(f"OSRM Routing Error ({lat1},{lon1} -> {lat2},{lon2}): {e}")
            return None
