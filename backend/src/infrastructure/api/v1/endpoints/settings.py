"""Settings & Configuration Endpoints (DB-backed, FR-SETTINGS-*)."""
import os
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.src.infrastructure.api.v1.dependencies import get_current_user, CurrentUser, require_role
from backend.src.infrastructure.persistence.sqlalchemy.database import get_db
from backend.src.domain.entities.app_setting import AppSetting

router = APIRouter(prefix="/settings", tags=["Settings & Configuration"])

DEFAULT_SYSTEM = {
    "app_name": os.getenv("APP_NAME", "MiniTMS"),
    "default_currency": "EUR",
    "default_language": "ru",
    "max_email_per_hour": 50,
    "email_delay_seconds": 30,
    "fuel_price_per_liter": 1.65,
    "default_profit_margin": 15.0,
    "gps_sync_interval_minutes": 5,
    "scraping_interval_minutes": 30,
    "timezone": "Europe/Kiev",
    "date_format": "DD.MM.YYYY",
}

DEFAULT_USER = {
    "language": "ru",
    "theme": "dark",
    "notifications_enabled": True,
    "email_notifications": True,
    "dashboard_layout": "default",
    "items_per_page": 25,
}


def _load(db, key, defaults):
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if row and isinstance(row.value, dict):
        return {**defaults, **row.value}
    return dict(defaults)


def _save(db, key, data):
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if row:
        row.value = data
    else:
        db.add(AppSetting(key=key, value=data))
    db.commit()


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


@router.get("", response_model=SystemSettings)
async def get_system_settings(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    s = _load(db, "system", DEFAULT_SYSTEM)
    s["updated_at"] = datetime.utcnow().isoformat()
    return SystemSettings(**s)


@router.put("", response_model=SystemSettings)
async def update_system_settings(
    update: SystemSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(['administrator', 'director'])),
):
    s = _load(db, "system", DEFAULT_SYSTEM)
    for field, value in update.dict(exclude_none=True).items():
        s[field] = value
    _save(db, "system", s)
    s["updated_at"] = datetime.utcnow().isoformat()
    return SystemSettings(**s)


@router.get("/user", response_model=UserSettings)
async def get_user_settings(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    u = _load(db, "user:" + str(current_user.id), DEFAULT_USER)
    u["user_id"] = current_user.id
    u["updated_at"] = datetime.utcnow().isoformat()
    return UserSettings(**u)


@router.put("/user", response_model=UserSettings)
async def update_user_settings(
    update: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    key = "user:" + str(current_user.id)
    u = _load(db, key, DEFAULT_USER)
    for field, value in update.dict(exclude_none=True).items():
        u[field] = value
    _save(db, key, u)
    u["user_id"] = current_user.id
    u["updated_at"] = datetime.utcnow().isoformat()
    return UserSettings(**u)
