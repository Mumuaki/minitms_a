from dataclasses import dataclass

from backend.src.application.ports.mobile_settings_provider_port import (
    MobileSettingsProviderPort,
)


@dataclass
class MobileProfitabilityThresholdResult:
    min_acceptable_rate: float


class GetMobileProfitabilityThresholdUseCase:
    def __init__(self, settings_provider_port: MobileSettingsProviderPort):
        self._settings_provider_port = settings_provider_port

    def execute(self) -> MobileProfitabilityThresholdResult:
        value = self._settings_provider_port.get_min_acceptable_rate()
        return MobileProfitabilityThresholdResult(min_acceptable_rate=value)
