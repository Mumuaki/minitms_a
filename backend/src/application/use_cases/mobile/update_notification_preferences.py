from dataclasses import dataclass

from backend.src.application.ports.mobile_notification_preferences_repository_port import (
    MobileNotificationPreferencesRepositoryPort,
)


@dataclass
class NotificationPreferencesUpdateResult:
    user_id: str
    preferences: dict


class UpdateMobileNotificationPreferencesUseCase:
    def __init__(self, preferences_repository_port: MobileNotificationPreferencesRepositoryPort):
        self._preferences_repository_port = preferences_repository_port

    def execute(self, user_id: str, preferences: dict) -> NotificationPreferencesUpdateResult:
        stored = self._preferences_repository_port.save_preferences(
            user_id=user_id,
            preferences=preferences,
        )
        return NotificationPreferencesUpdateResult(user_id=user_id, preferences=stored)
