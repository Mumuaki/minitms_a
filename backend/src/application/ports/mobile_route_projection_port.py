from typing import Protocol


class MobileRouteProjectionPort(Protocol):
    def get_route_projection(self, *, cargo_id: str) -> dict:
        ...
