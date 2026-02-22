from backend.src.infrastructure.config.settings import Settings


class MobileSettingsProviderAdapter:
    def __init__(self, settings: Settings | None = None):
        self._settings = settings or Settings()

    def get_min_acceptable_rate(self) -> float:
        return float(self._settings.MIN_ACCEPTABLE_RATE)
