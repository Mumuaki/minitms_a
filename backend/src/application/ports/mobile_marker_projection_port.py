from typing import Protocol


class MobileMarkerProjectionPort(Protocol):
    def get_markers(self, *, cargo_id: str) -> list[dict]:
        ...
