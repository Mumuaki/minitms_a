"""
Settings & Configuration Endpoints.

Эндпоинты:
- GET   /settings       — системные настройки
- PUT   /settings       — обновить системные настройки
- GET   /settings/user  — настройки текущего пользователя
- PUT   /settings/user  — обновить настройки пользователя
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from backend.src.infrastructure.api.v1.dependencies import get_current_user, CurrentUser

router = APIRouter(prefix="/settings", tags=["Settings & Configuration"])

# In-memory store (replace with DB-backed model as needed)
_system_settings: Dict[str, Any] = {
    "app_name": os.getenv("APP_NAME", "MiniTMS"),
    "default_currency": "EUR",
    "default_language": "uk",
    "max_email_per_hour": 50,
    "email_delay_seconds": 30,
    "fuel_price_per_liter": 1.65,
    "default_profit_margin": 15.0,
    "gps_sync_interval_minutes": 5,
    "scraping_interval_minutes": 30,
    "timezone": "Europe/Kiev",
    "date_format": "DD.MM.YYYY",
    "updated_at": datetime.utcnow().isoformat(),
}

_user_settings: Dict[int, Dict[str, Any]] = {}


# ── Schemas ───────────────────────────────────────────────────────────────────

class SystemSettings(BaseModel):
    app_name: str
    default_currency: str
    default_language: str
    max_email_per_hour: int
    email_delay_seconds: int
    fuel_price_per_liter: float
    default_profit_margin: float
    gps_sync_interval_minutes: int
    scraping_interval_minutes: int
    timezone: str
    date_format: str
    updated_at: str


class SystemSettingsUpdate(BaseModel):
    default_currency: Optional[str] = None
    default_language: Optional[str] = None
    max_email_per_hour: Optional[int] = None
    email_delay_seconds: Optional[int] = None
    fuel_price_per_liter: Optional[float] = None
    default_profit_margin: Optional[float] = None
    gps_sync_interval_minutes: Optional[int] = None
    scraping_interval_minutes: Optional[int] = None
    timezone: Optional[str] = None
    date_format: Optional[str] = None


class UserSettings(BaseModel):
    user_id: int
    language: str
    theme: str
    notifications_enabled: bool
    email_notifications: bool
    dashboard_layout: str
    items_per_page: int
    updated_at: str


class UserSettingsUpdate(BaseModel):
    language: Optional[str] = None
    theme: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    dashboard_layout: Optional[str] = None
    items_per_page: Optional[int] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=SystemSettings)
async def get_system_settings(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Системные настройки приложения."""
    return SystemSettings(**_system_settings)


@router.put("", response_model=SystemSettings)
async def update_system_settings(
    update: SystemSettingsUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Обновить системные настройки (только admin)."""
    for field, value in update.dict(exclude_none=True).items():
        _system_settings[field] = value
    _system_settings["updated_at"] = datetime.utcnow().isoformat()
    return SystemSettings(**_system_settings)


@router.get("/user", response_model=UserSettings)
async def get_user_settings(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Настройки текущего пользователя."""
    defaults = {
        "user_id": current_user.id,
        "language": "uk",
        "theme": "dark",
        "notifications_enabled": True,
        "email_notifications": True,
        "dashboard_layout": "default",
        "items_per_page": 25,
        "updated_at": datetime.utcnow().isoformat(),
    }
    stored = _user_settings.get(current_user.id, {})
    merged = {**defaults, **stored}
    return UserSettings(**merged)


@router.put("/user", response_model=UserSettings)
async def update_user_settings(
    update: UserSettingsUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Обновить настройки текущего пользователя."""
    existing = _user_settings.get(current_user.id, {
        "user_id": current_user.id,
        "language": "uk",
        "theme": "dark",
        "notifications_enabled": True,
        "email_notifications": True,
        "dashboard_layout": "default",
        "items_per_page": 25,
    })
    for field, value in update.dict(exclude_none=True).items():
        existing[field] = value
    existing["updated_at"] = datetime.utcnow().isoformat()
    _user_settings[current_user.id] = existing
    return UserSettings(**existing)
