class MarkerProjectionAdapter:
    def get_markers(self, *, cargo_id: str) -> list[dict]:
        return [
            {"type": "A", "cargo_id": cargo_id, "latitude": 50.4501, "longitude": 30.5234},
            {"type": "B", "cargo_id": cargo_id, "latitude": 51.1079, "longitude": 17.0385},
            {"type": "C", "cargo_id": cargo_id, "latitude": 52.2297, "longitude": 21.0122},
        ]
