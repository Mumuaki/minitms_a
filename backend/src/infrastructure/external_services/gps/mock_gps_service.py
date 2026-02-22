import random
from datetime import datetime, timezone
from typing import Optional, Tuple
from backend.src.domain.services.gps_service import GpsService

class MockGpsService(GpsService):
    def get_vehicle_location(self, tracker_id: str) -> Tuple[Optional[str], Optional[datetime]]:
        # Simulate API call with predefined cities
        cities = [
            "Berlin, DE", "Paris, FR", "Warsaw, PL", "Prague, CZ", 
            "Bratislava, SK", "Vienna, AT", "Budapest, HU", "Dortmund, DE",
            "Munich, DE", "Milan, IT", "Barcelona, ES", "Lyon, FR"
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
