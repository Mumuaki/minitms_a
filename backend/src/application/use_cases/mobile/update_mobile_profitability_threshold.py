from backend.src.application.ports.mobile_settings_repository_port import (
    MobileSettingsRepositoryPort,
)


class MobileThresholdValidator:
    @staticmethod
    def validate(value: float) -> float:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            raise ValueError("Mobile profitability threshold must be numeric")

        if numeric_value < 0.15 or numeric_value > 3.5:
            raise ValueError("Mobile profitability threshold must be in range 0.15..3.5")
        return numeric_value


class UpdateMobileProfitabilityThresholdUseCase:
    def __init__(self, settings_repository_port: MobileSettingsRepositoryPort):
        self._settings_repository_port = settings_repository_port

    def execute(self, value: float) -> float:
        validated = MobileThresholdValidator.validate(value)
        return self._settings_repository_port.save_min_acceptable_rate(value=validated)
