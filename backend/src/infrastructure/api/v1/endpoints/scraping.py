"""
Trans.eu Scraping Status Endpoints.

Эндпоинты:
- GET /scraping/status — статус скрапера Trans.eu
- POST /scraping/start — запустить скрапинг вручную
- POST /scraping/stop  — остановить скрапер
"""

import os
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from backend.src.infrastructure.api.v1.dependencies import get_current_user

router = APIRouter(prefix="/scraping", tags=["Trans.eu Scraping"])

TRANS_EU_USERNAME = os.getenv("TRANS_EU_USERNAME", "")
HEADLESS_MODE = os.getenv("HEADLESS_MODE", "True").lower() == "true"

# In-memory scraper state
_scraper_state = {
    "status": "idle",
    "last_run": None,
    "last_success": None,
    "cargos_fetched": 0,
    "errors": 0,
    "is_running": False,
}


class ScrapingStatus(BaseModel):
    status: str
    is_running: bool
    configured: bool
    trans_eu_username: Optional[str] = None
    headless_mode: bool
    last_run: Optional[str] = None
    last_success: Optional[str] = None
    cargos_fetched: int
    errors: int
    message: str


@router.get("/status", response_model=ScrapingStatus)
async def get_scraping_status(
    current_user=Depends(get_current_user),
):
    """Статус скрапера Trans.eu."""
    configured = bool(TRANS_EU_USERNAME)
    masked_user = (TRANS_EU_USERNAME[:4] + "***") if TRANS_EU_USERNAME else None

    return ScrapingStatus(
        status=_scraper_state["status"],
        is_running=_scraper_state["is_running"],
        configured=configured,
        trans_eu_username=masked_user,
        headless_mode=HEADLESS_MODE,
        last_run=_scraper_state["last_run"],
        last_success=_scraper_state["last_success"],
        cargos_fetched=_scraper_state["cargos_fetched"],
        errors=_scraper_state["errors"],
        message="Scraper ready" if configured else "Set TRANS_EU_USERNAME and TRANS_EU_PASSWORD in .env",
    )


@router.post("/start", status_code=status.HTTP_200_OK)
async def start_scraping(
    current_user=Depends(get_current_user),
):
    """Запустить скрапинг вручную."""
    if _scraper_state["is_running"]:
        return {"status": "already_running", "message": "Scraper is already running"}

    _scraper_state["is_running"] = True
    _scraper_state["status"] = "running"
    _scraper_state["last_run"] = datetime.utcnow().isoformat()

    return {"status": "started", "message": "Scraping started", "started_at": _scraper_state["last_run"]}


@router.post("/stop", status_code=status.HTTP_200_OK)
async def stop_scraping(
    current_user=Depends(get_current_user),
):
    """Остановить скрапер."""
    _scraper_state["is_running"] = False
    _scraper_state["status"] = "idle"
    return {"status": "stopped", "message": "Scraper stopped"}
