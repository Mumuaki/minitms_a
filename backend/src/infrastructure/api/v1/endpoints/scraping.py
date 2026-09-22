"""
Trans.eu Scraping Status Endpoints.

Эндпоинты:
- GET /scraping/status — статус скрапера Trans.eu
- POST /scraping/start — запустить скрапинг вручную
- POST /scraping/stop  — остановить скрапер
"""

import os
import asyncio
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from backend.src.infrastructure.api.v1.dependencies import get_current_user, require_role

from typing import List
from fastapi import Query, HTTPException
from sqlalchemy.orm import Session
from backend.src.infrastructure.persistence.sqlalchemy.database import get_db, SessionLocal
from backend.src.domain.repositories.cargo_repository import CargoRepository
from backend.src.infrastructure.persistence.sqlalchemy.repositories.cargo_repository_impl import CargoRepositoryImpl
from backend.src.application.use_cases.cargo.import_trans_eu_offers import ImportTransEuOffersUseCase

def get_cargo_repository(db: Session = Depends(get_db)) -> CargoRepository:
    return CargoRepositoryImpl(db)

def get_import_trans_eu_offers_use_case(repo: CargoRepository = Depends(get_cargo_repository)) -> ImportTransEuOffersUseCase:
    return ImportTransEuOffersUseCase(repo)

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

# Асинхронные задания ручного импорта: job_id -> status
_MANUAL_JOBS: Dict[str, Dict[str, Any]] = {}


async def _run_manual_import_job(job_id: str, timeout_seconds: int) -> None:
    """Фоновое выполнение полуавтоматического импорта Trans.eu."""
    job = _MANUAL_JOBS.get(job_id)
    if not job:
        return
    job["status"] = "waiting_search"
    db = SessionLocal()
    try:
        repo = CargoRepositoryImpl(db)
        use_case = ImportTransEuOffersUseCase(repo)
        result = await use_case.execute_manual(timeout_seconds=timeout_seconds, db=db)
        job["status"] = "done"
        job["saved"] = len(result)
        job["total"] = len(result)
        job["message"] = "Сохранено грузов: %d" % len(result)
    except Exception as e:
        job["status"] = "error"
        job["message"] = str(e)[:500]
    finally:
        db.close()


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
    current_user=Depends(require_role(['administrator','director','dispatcher'])),
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
    current_user=Depends(require_role(['administrator','director','dispatcher'])),
):
    """Остановить скрапер."""
    _scraper_state["is_running"] = False
    _scraper_state["status"] = "idle"
    return {"status": "stopped", "message": "Scraper stopped"}

@router.post(
    "/import_trans_eu",
    response_model=List[dict],
    summary="Запуск импорта из Trans.eu",
    description="Запускает скрапинг Trans.eu по заданным параметрам и сохраняет результаты в БД."
)
async def import_trans_eu(
    current_user = Depends(require_role(["administrator", "director", "dispatcher"])),
    loading: str = Query(..., description="Место загрузки"),
    unloading: Optional[str] = Query(None, description="Место выгрузки"),
    loading_radius: int = Query(75, description="Радиус загрузки"),
    unloading_radius: int = Query(75, description="Радиус выгрузки"),
    date_from: Optional[str] = Query(None, description="Дата загрузки с (DD.MM.YYYY)"),
    date_to: Optional[str] = Query(None, description="Дата загрузки по (DD.MM.YYYY)"),
    unloading_date_from: Optional[str] = Query(None, description="Дата выгрузки с (DD.MM.YYYY)"),
    unloading_date_to: Optional[str] = Query(None, description="Дата выгрузки по (DD.MM.YYYY)"),
    weight_to: str = Query("0.9", description="Макс вес"),
    length_to: Optional[str] = Query(None, description="Макс длина"),
    use_case: ImportTransEuOffersUseCase = Depends(get_import_trans_eu_offers_use_case),
    db: Session = Depends(get_db),
):
    try:
        result = await use_case.execute(
            loading=loading,
            unloading=unloading,
            loading_radius=loading_radius,
            unloading_radius=unloading_radius,
            date_from=date_from,
            date_to=date_to,
            unloading_date_from=unloading_date_from,
            unloading_date_to=unloading_date_to,
            weight_to=weight_to,
            length_to=length_to,
            db=db
        )
        return [c.dict() for c in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/import_trans_eu_manual",
    summary="Полуавтоматический импорт из Trans.eu (асинхронно)",
    description="Запускает импорт в фоне. Оператор вручную выполняет поиск в браузере, "
                "скрапер сам парсит результат. Статус: GET /scraping/import_trans_eu_manual/{job_id}/status"
)
async def import_trans_eu_manual(
    current_user = Depends(require_role(["administrator", "director", "dispatcher"])),
    timeout_seconds: int = Query(600, description="Сколько секунд ждать ручной поиск"),
):
    # Один ручной импорт за раз — браузер общий
    for j in _MANUAL_JOBS.values():
        if j.get("status") in ("queued", "waiting_search", "parsing"):
            raise HTTPException(status_code=409, detail="Импорт уже выполняется. Дождитесь завершения.")

    job_id = str(uuid.uuid4())[:8]
    _MANUAL_JOBS[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "saved": 0,
        "total": 0,
        "message": "Импорт запущен",
        "started_at": datetime.utcnow().isoformat(),
    }
    asyncio.create_task(_run_manual_import_job(job_id, timeout_seconds))
    return _MANUAL_JOBS[job_id]


@router.get(
    "/import_trans_eu_manual/{job_id}/status",
    summary="Статус асинхронного импорта Trans.eu",
)
async def import_trans_eu_manual_status(
    job_id: str,
    current_user = Depends(require_role(["administrator", "director", "dispatcher"])),
):
    job = _MANUAL_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    return job

