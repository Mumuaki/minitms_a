from dataclasses import dataclass

from backend.src.application.ports.mobile_route_projection_port import (
    MobileRouteProjectionPort,
)


@dataclass
class MobileRouteView:
    cargo_id: str
    route_points: list[dict]


class ViewSelectedCargoRouteUseCase:
    def __init__(self, route_projection_port: MobileRouteProjectionPort):
        self._route_projection_port = route_projection_port

    def execute(self, cargo_id: str) -> MobileRouteView:
        projection = self._route_projection_port.get_route_projection(cargo_id=cargo_id)
        return MobileRouteView(
            cargo_id=projection.get("cargo_id", cargo_id),
            route_points=projection.get("route_points", []),
        )
