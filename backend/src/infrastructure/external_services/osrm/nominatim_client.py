import httpx
import logging
from typing import Optional, Tuple
from backend.src.infrastructure.utils.retry_utils import async_retry, TransientError, RateLimitError

logger = logging.getLogger(__name__)

class NominatimClient:
    """
    Client for OpenStreetMap Nominatim API (Geocoding).
    """
    BASE_URL = "https://nominatim.openstreetmap.org/search"
    USER_AGENT = "MiniTMS/1.0 (internal-testing)"
    _cache: dict = {}

    @async_retry(max_retries=3, backoff_factor=2)
    async def _fetch_data(self, address: str) -> list:
        headers = {"User-Agent": self.USER_AGENT}
        params = {"q": address, "format": "json", "limit": 1}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.BASE_URL, params=params, headers=headers, timeout=10.0)
                if response.status_code == 429:
                    raise RateLimitError("Nominatim Rate Limit Exceeded")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise TransientError(f"Nominatim HTTP Error: {e}") from e

    async def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        if not address:
            return None
            
        if address in self._cache:
            logger.debug(f"Nominatim Cache hit for '{address}'")
            return self._cache[address]

        try:
            data = await self._fetch_data(address)
            if not data:
                logger.warning(f"Nominatim: Address not found: {address}")
                return None
            
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            
            logger.info(f"Geocoded '{address}' -> ({lat}, {lon})")
            self._cache[address] = (lat, lon)
            return lat, lon
                
        except Exception as e:
            logger.error(f"Nominatim Geocoding Error for '{address}': {e}")
            return None
