class MobileGpsProviderAdapter:
    """Contract stub for Slice-4 integration stage."""

    def get_positions(self) -> list[dict]:
        return [
            {
                "vehicle_id": "veh-001",
                "latitude": 50.4501,
                "longitude": 30.5234,
                "freshness_seconds": 45,
            }
        ]
