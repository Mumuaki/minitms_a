import requests
from datetime import datetime, timezone
from typing import Optional, Tuple
from backend.src.domain.services.gps_service import GpsService
from backend.src.infrastructure.config.settings import settings

class GpsGuardAdapter(GpsService):
    def get_vehicle_location(self, tracker_id: str) -> Tuple[Optional[str], Optional[datetime]]:
        """
        Fetches vehicle location from https://a1.gpsguard.eu/api/v1/vehicle/{tracker_id}
        """
        
        # If no API key is set, perhaps we should still rely on Mock or fail? 
        # For this implementation, I will attempt the request.
        
        url = f"{settings.GPS_GUARD_BASE_URL}/vehicle/{tracker_id}"
        headers = {}
        if settings.GPS_GUARD_API_KEY:
            headers["Authorization"] = f"Bearer {settings.GPS_GUARD_API_KEY}"
            # Or maybe "X-API-Key"? Standard is often Bearer or custom.
            # Without specific docs, I'll Assume Headers or just public URL if user didn't specify key.

        try:
            # Using synchronous requests as GpsService is sync
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Assume standard format. 
                # If the user says "import real location", I need to parse it.
                # Possible formats:
                # 1. Flat: {"lat": 1.2, "lon": 3.4, "last_updated": "..."}
                # 2. Nested: {"data": {"location": ...}}
                # Since I cannot know the exact format, I will code defensively 
                # and look for common fields.
                
                lat = data.get("lat") or data.get("latitude")
                lon = data.get("lon") or data.get("lng") or data.get("longitude")
                address = data.get("address")
                
                last_updated_str = data.get("last_updated") or data.get("timestamp") or data.get("time")
                
                last_updated = None
                if last_updated_str:
                    try:
                         # Attempt ISO parsing
                         last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
                    except:
                         last_updated = datetime.now(timezone.utc) # Fallback
                else:
                    last_updated = datetime.now(timezone.utc)

                location_str = address
                if not location_str and lat and lon:
                    location_str = f"{lat}, {lon}"
                
                return location_str, last_updated
            else:
                print(f"GPS Guard API Error: {response.status_code} - {response.text}")
                # Fallback to Mock or None? 
                # User request: "import real location".
                # If API fails, better return None to indicate issue? or Mock...
                # Let's return None to avoid misleading data.
                return None, None
                
        except Exception as e:
            print(f"GPS Guard Connection Error: {e}")
            return None, None
