from backend.src.infrastructure.config.settings import Settings


class MobileSettingsRepositoryAdapter:
    def __init__(
        self,
        settings: Settings | None = None,
    ):
        self._settings = settings or Settings()
        self._last_saved_min_acceptable_rate: float | None = None

    def save_min_acceptable_rate(self, *, value: float) -> float:
        saved = float(value)
        if saved < 0.15 or saved > 3.5:
            raise ValueError("MIN_ACCEPTABLE_RATE must be in range 0.15..3.5")
        self._last_saved_min_acceptable_rate = saved
        self._settings.MIN_ACCEPTABLE_RATE = saved
        return saved
