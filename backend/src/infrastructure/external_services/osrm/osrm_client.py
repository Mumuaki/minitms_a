import httpx
import logging
from typing import Optional, Tuple
from backend.src.infrastructure.utils.retry_utils import async_retry, TransientError, RateLimitError

logger = logging.getLogger(__name__)

class OSRMClient:
    """
    Client for OSRM (Open Source Routing Machine).
    Uses public demo server by default (router.project-osrm.org).
    """
    BASE_URL = "http://router.project-osrm.org/route/v1/driving"

    @async_retry(max_retries=3, backoff_factor=2)
    async def _fetch_data(self, url: str, params: dict) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                if response.status_code == 429:
                    raise RateLimitError("OSRM Rate Limit Exceeded")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise TransientError(f"OSRM HTTP Error: {e}") from e

    async def get_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[float]:
        try:
            coords = f"{lon1},{lat1};{lon2},{lat2}"
            url = f"{self.BASE_URL}/{coords}"
            params = {"overview": "false", "steps": "false"}
            
            data = await self._fetch_data(url, params)
            if data.get("code") != "Ok" or not data.get("routes"):
                logger.error(f"OSRM Error: {data.get('code')}")
                return None
            
            meters = data["routes"][0]["distance"]
            km = meters / 1000.0
            return round(km, 2)
                
        except Exception as e:
            logger.error(f"OSRM Routing Error ({lat1},{lon1} -> {lat2},{lon2}): {e}")
            return None

    async def get_route_info(self, lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[Tuple[float, str]]:
        try:
            coords = f"{lon1},{lat1};{lon2},{lat2}"
            url = f"{self.BASE_URL}/{coords}"
            params = {"overview": "simplified", "steps": "false"}
            
            data = await self._fetch_data(url, params)
            if data.get("code") != "Ok" or not data.get("routes"):
                logger.error(f"OSRM Error: {data.get('code')}")
                return None
            
            route = data["routes"][0]
            km = route["distance"] / 1000.0
            polyline = route.get("geometry", "")
            return round(km, 2), polyline
                
        except Exception as e:
            logger.error(f"OSRM Routing Error ({lat1},{lon1} -> {lat2},{lon2}): {e}")
            return None
