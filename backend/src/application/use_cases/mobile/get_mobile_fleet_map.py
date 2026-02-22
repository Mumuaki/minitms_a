from dataclasses import dataclass

from backend.src.application.ports.mobile_gps_position_provider_port import (
    MobileGpsPositionProviderPort,
)


@dataclass
class MobileFleetPosition:
    vehicle_id: str
    latitude: float
    longitude: float
    freshness_seconds: int


class GetMobileFleetMapUseCase:
    def __init__(self, gps_position_provider_port: MobileGpsPositionProviderPort):
        self._gps_position_provider_port = gps_position_provider_port

    def execute(self) -> list[MobileFleetPosition]:
        positions = self._gps_position_provider_port.get_positions()
        return [
            MobileFleetPosition(
                vehicle_id=str(item.get("vehicle_id", "")),
                latitude=self._to_float(item.get("latitude")),
                longitude=self._to_float(item.get("longitude")),
                freshness_seconds=self._to_int(item.get("freshness_seconds")),
            )
            for item in positions
        ]

    @staticmethod
    def _to_float(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _to_int(value: object) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
