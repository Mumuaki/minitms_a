from typing import Protocol


class MobileSettingsProviderPort(Protocol):
    def get_min_acceptable_rate(self) -> float:
        ...
