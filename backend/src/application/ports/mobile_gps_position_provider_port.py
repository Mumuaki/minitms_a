from typing import Protocol


class MobileGpsPositionProviderPort(Protocol):
    def get_positions(self) -> list[dict]:
        ...
