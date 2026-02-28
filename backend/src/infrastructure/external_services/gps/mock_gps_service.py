import random
from datetime import datetime, timezone
from typing import Optional, Tuple
from backend.src.domain.services.gps_service import GpsService

class MockGpsService(GpsService):
    def get_vehicle_location(self, tracker_id: str) -> Tuple[Optional[str], Optional[datetime]]:
        # Simulate API call with predefined cities in format "ISO-2, postal code, city"
        cities = [
            "DE, 10115, Berlin", "FR, 75001, Paris", "PL, 00-001, Warsaw", "CZ, 110 00, Prague", 
            "SK, 811 01, Bratislava", "AT, 1010, Vienna", "HU, 1014, Budapest", "DE, 44137, Dortmund",
            "DE, 80331, Munich", "IT, 20121, Milan", "ES, 08001, Barcelona", "FR, 69001, Lyon"
        ]
        
        # Deterministic selection based on tracker_id characters
        # This ensures the same tracker always returns the same city (unless we want to simulate movement)
        # Sum of ASCII values of characters
        idx = sum(ord(c) for c in tracker_id) % len(cities)
        location = cities[idx]
        
        # Override for specific demo IDs if needed
        if tracker_id == "TRK-999":
             location = "Bratislava, SK"
        
        # Return current UTC time
        now = datetime.now(timezone.utc)
        
        return location, now
