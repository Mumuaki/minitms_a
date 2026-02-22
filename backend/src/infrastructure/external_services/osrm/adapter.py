from typing import Optional, Tuple
import logging
from backend.src.application.ports.maps_port import MapsPort
from backend.src.infrastructure.external_services.osrm.nominatim_client import NominatimClient
from backend.src.infrastructure.external_services.osrm.osrm_client import OSRMClient

logger = logging.getLogger(__name__)

class OSRMMapsAdapter(MapsPort):
    """
    Implementation of MapsPort using OpenStreetMap services:
    - Nominatim for Geocoding
    - OSRM for Routing/Distance
    """
    
    def __init__(self):
        self.nominatim = NominatimClient()
        self.osrm = OSRMClient()

    async def calculate_distance(self, origin: str, destination: str) -> float:
        """
        Calculates distance in km between two addresses.
        Returns 0.0 if calculation fails.
        """
        # 1. Geocode Origin
        origin_coords = await self.nominatim.get_coordinates(origin)
        if not origin_coords:
            logger.warning(f"Could not geocode origin: {origin}")
            return 0.0

        # 2. Geocode Destination
        dest_coords = await self.nominatim.get_coordinates(destination)
        if not dest_coords:
            logger.warning(f"Could not geocode destination: {destination}")
            return 0.0

        # 3. Calculate Distance
        distance = await self.osrm.get_distance(
            origin_coords[0], origin_coords[1],
            dest_coords[0], dest_coords[1]
        )
        
        return distance if distance else 0.0

    async def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Returns (lat, lon) for address.
        """
        return await self.nominatim.get_coordinates(address)
