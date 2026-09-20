"""Notification Endpoints (FR-NOTIFY-003/004)."""
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.src.infrastructure.api.v1.dependencies import get_current_user, CurrentUser
from backend.src.domain.services.notification_limiter import NotificationLimiter, COOLDOWN_SECONDS

router = APIRouter(prefix="/notifications", tags=["Notifications"])

_prefs: Dict[int, Dict[str, Any]] = {}
DEFAULT_PREFS = {
    "profitable_cargo": True,
    "plan_alert": True,
    "email_digest": False,
    "push_enabled": True,
}
_limiter = NotificationLimiter()


class NotificationPreferences(BaseModel):
    user_id: int
    profitable_cargo: bool
    plan_alert: bool
    email_digest: bool
    push_enabled: bool
    cooldown_seconds: int
    cooldown_remaining: int


class NotificationPreferencesUpdate(BaseModel):
    profitable_cargo: Optional[bool] = None
    plan_alert: Optional[bool] = None
    email_digest: Optional[bool] = None
    push_enabled: Optional[bool] = None


def _get_prefs(user_id):
    return {**DEFAULT_PREFS, **_prefs.get(user_id, {})}


def _response(user_id):
    prefs = _get_prefs(user_id)
    return NotificationPreferences(
        user_id=user_id,
        profitable_cargo=prefs["profitable_cargo"],
        plan_alert=prefs["plan_alert"],
        email_digest=prefs["email_digest"],
        push_enabled=prefs["push_enabled"],
        cooldown_seconds=COOLDOWN_SECONDS,
        cooldown_remaining=_limiter.remaining(user_id),
    )


@router.get("/preferences", response_model=NotificationPreferences)
async def get_notification_preferences(current_user: CurrentUser = Depends(get_current_user)):
    return _response(current_user.id)


@router.put("/preferences", response_model=NotificationPreferences)
async def update_notification_preferences(
    update: NotificationPreferencesUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    existing = _prefs.get(current_user.id, {})
    for field, value in update.dict(exclude_none=True).items():
        existing[field] = value
    _prefs[current_user.id] = existing
    return _response(current_user.id)
