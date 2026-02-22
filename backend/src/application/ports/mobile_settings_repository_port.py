from typing import Protocol


class MobileSettingsRepositoryPort(Protocol):
    def save_min_acceptable_rate(self, *, value: float) -> float:
        ...
