from typing import Protocol


class MobileNotificationPreferencesRepositoryPort(Protocol):
    def save_preferences(self, *, user_id: str, preferences: dict) -> dict:
        ...
