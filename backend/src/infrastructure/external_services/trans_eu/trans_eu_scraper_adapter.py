"""
Адаптер для взаимодействия со скрапером Trans.eu.
Реализует TransEuScraperPort.
"""

from typing import List, Dict, Any
from backend.src.application.ports.scraping_port import TransEuScraperPort
from backend.src.infrastructure.external_services.trans_eu.client import TransEuClient
from backend.src.infrastructure.utils.retry_utils import async_retry, TransientError, RateLimitError, PermanentError

class TransEuScraperAdapter(TransEuScraperPort):
    """
    Адаптер, оборачивающий существующий TransEuClient.
    """
    
    def __init__(self):
        self._client = None
        
    async def _get_client(self) -> TransEuClient:
        if not self._client:
            self._client = await TransEuClient.get_instance()
            await self._client.start()
        return self._client

    async def login(self) -> bool:
        client = await self._get_client()
        return await client.login()

    @async_retry(max_retries=3, backoff_factor=2)
    async def fetch_offers(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        client = await self._get_client()
        
        loading_location = criteria.get("loading_location", "")
        unloading_location = criteria.get("unloading_location", None)
        loading_radius = criteria.get("loading_radius", 75)
        unloading_radius = criteria.get("unloading_radius", 75)
        date_from = criteria.get("date_from", None)
        date_to = criteria.get("date_to", None)
        unloading_date_from = criteria.get("unloading_date_from", None)
        unloading_date_to = criteria.get("unloading_date_to", None)
        weight_to = criteria.get("weight_to", "0.9")
        length_to = criteria.get("length_to", "4.8")
        
        try:
            results = await client.search_offers(
                loading_location=loading_location,
                unloading_location=unloading_location,
                loading_radius=loading_radius,
                unloading_radius=unloading_radius,
                date_from=date_from,
                date_to=date_to,
                unloading_date_from=unloading_date_from,
                unloading_date_to=unloading_date_to,
                weight_to=weight_to,
                length_to=length_to
            )
            return results if results else []
        except Exception as e:
            error_str = str(e).lower()
            if "timeout" in error_str or "net::err" in error_str or "target closed" in error_str or "disconnected" in error_str:
                raise TransientError(f"Scraper transient error: {e}") from e
            elif "cloudflare" in error_str or "captcha" in error_str or "429" in error_str:
                raise RateLimitError(f"Scraper rate limit: {e}") from e
            else:
                raise PermanentError(f"Scraper permanent error: {e}") from e

