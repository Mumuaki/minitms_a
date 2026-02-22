from abc import ABC, abstractmethod
from typing import Optional, Tuple
from datetime import datetime

class GpsService(ABC):
    @abstractmethod
    def get_vehicle_location(self, tracker_id: str) -> Tuple[Optional[str], Optional[datetime]]:
        """
        Returns (location_string, last_updated_datetime)
        location_string can be "Lat, Lon" or address.
        """
        pass
