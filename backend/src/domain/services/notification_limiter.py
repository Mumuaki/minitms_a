"""Лимитер уведомлений: не чаще 1 раза в 5 минут на пользователя (FR-NOTIFY-004 / BR-014)."""
import time

COOLDOWN_SECONDS = 300


class NotificationLimiter:
    def __init__(self):
        self._last = {}  # user_id -> last sent timestamp

    def allowed(self, user_id, now=None):
        now = now if now is not None else time.time()
        last = self._last.get(user_id)
        return last is None or (now - last) >= COOLDOWN_SECONDS

    def record(self, user_id, now=None):
        now = now if now is not None else time.time()
        self._last[user_id] = now
        return now

    def remaining(self, user_id, now=None):
        now = now if now is not None else time.time()
        last = self._last.get(user_id)
        if last is None:
            return 0
        return max(0, int(COOLDOWN_SECONDS - (now - last)))
