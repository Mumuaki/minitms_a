from dataclasses import dataclass

from backend.src.application.ports.mobile_marker_projection_port import (
    MobileMarkerProjectionPort,
)


@dataclass
class MobileMapMarkersResult:
    cargo_id: str
    markers: list[dict]


class GetMobileMapMarkersUseCase:
    def __init__(self, marker_projection_port: MobileMarkerProjectionPort):
        self._marker_projection_port = marker_projection_port

    def execute(self, cargo_id: str) -> MobileMapMarkersResult:
        markers = self._marker_projection_port.get_markers(cargo_id=cargo_id)
        return MobileMapMarkersResult(cargo_id=cargo_id, markers=markers)
