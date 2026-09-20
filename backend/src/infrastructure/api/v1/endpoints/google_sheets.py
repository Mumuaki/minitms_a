"""
Google Sheets Integration Endpoints.

Эндпоинты:
- GET  /integrations/google-sheets/status — статус подключения
- POST /integrations/google-sheets/sync   — запустить синхронизацию
- GET  /integrations/google-sheets/sync   — статус последней синхронизации
"""

import os
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.src.infrastructure.api.v1.dependencies import get_current_user, require_role
from sqlalchemy.orm import Session
from backend.src.infrastructure.persistence.sqlalchemy.database import get_db
from backend.src.domain.entities.order import Order
from backend.src.infrastructure.persistence.sqlalchemy.models.cargo_model import Cargo
from backend.src.infrastructure.external_services.google_sheets.sheets_mapper import SHEETS_HEADERS, build_order_row

router = APIRouter(prefix="/integrations/google-sheets", tags=["Google Sheets Integration"])

GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "")
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")


def _configured(value):
    v = (value or "").strip()
    return bool(v) and v != "CHANGE_ME"

# Track last sync state in memory
_last_sync: Optional[dict] = None


# ── Schemas ───────────────────────────────────────────────────────────────────

class GoogleSheetsStatus(BaseModel):
    connected: bool
    spreadsheet_id: Optional[str] = None
    spreadsheet_url: Optional[str] = None
    columns_count: int
    last_sync: Optional[str] = None
    message: str


class SyncStatus(BaseModel):
    sync_id: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    rows_synced: int
    columns_synced: int
    errors: List[str]
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/status", response_model=GoogleSheetsStatus)
async def get_google_sheets_status(
    current_user=Depends(get_current_user),
):
    """Статус подключения к Google Sheets."""
    connected = _configured(GOOGLE_SHEETS_CREDENTIALS) and _configured(GOOGLE_SHEETS_ID)

    if connected:
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEETS_ID}"
        message = "Connected to Google Sheets"
    else:
        url = None
        message = "Google Sheets not configured. Set GOOGLE_SHEETS_CREDENTIALS and GOOGLE_SHEETS_ID in .env"

    return GoogleSheetsStatus(
        connected=connected,
        spreadsheet_id=GOOGLE_SHEETS_ID if connected else None,
        spreadsheet_url=url,
        columns_count=len(SHEETS_HEADERS),
        last_sync=_last_sync.get("completed_at") if _last_sync else None,
        message=message,
    )


@router.get("/sync", response_model=SyncStatus)
async def get_sync_status(
    current_user=Depends(get_current_user),
):
    """Статус последней синхронизации с Google Sheets."""
    if _last_sync:
        return SyncStatus(**_last_sync)

    return SyncStatus(
        sync_id="none",
        status="never_synced",
        started_at=None,
        completed_at=None,
        rows_synced=0,
        columns_synced=0,
        errors=[],
        message="No sync has been performed yet",
    )


@router.post("/sync", response_model=SyncStatus, status_code=status.HTTP_200_OK)
async def trigger_sync(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(['administrator','director'])),
):
    """Синхронизировать заказы с Google Sheets (25 столбцов, FR-GSHEET-*)."""
    global _last_sync

    if not (_configured(GOOGLE_SHEETS_CREDENTIALS) and _configured(GOOGLE_SHEETS_ID)):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Sheets not configured. Set GOOGLE_SHEETS_CREDENTIALS and GOOGLE_SHEETS_ID in .env",
        )

    import uuid
    now = datetime.utcnow().isoformat()
    sync_id = str(uuid.uuid4())[:8]
    rows_synced = 0
    errors: List[str] = []
    sync_status = "completed"

    try:
        import gspread
        from google.oauth2.service_account import Credentials
        import json

        creds_data = json.loads(GOOGLE_SHEETS_CREDENTIALS)
        creds = Credentials.from_service_account_info(creds_data, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(GOOGLE_SHEETS_ID).sheet1

        existing = sheet.get_all_values()
        if not existing:
            sheet.append_row(SHEETS_HEADERS)
            existing = sheet.get_all_values()

        orders = db.query(Order).order_by(Order.id.asc()).all()
        cargo_map = {}
        for order in orders:
            if order.cargo_id is not None and order.cargo_id not in cargo_map:
                cargo_map[order.cargo_id] = db.query(Cargo).filter(Cargo.id == order.cargo_id).first()

        for order in orders:
            cargo = cargo_map.get(order.cargo_id)
            row_index = len(existing) + 1 + rows_synced
            sheet.append_row(build_order_row(order, cargo, row_index))
            rows_synced += 1
    except ImportError:
        errors.append("gspread library not installed — install with: pip install gspread google-auth")
        sync_status = "partial"
    except Exception as e:
        errors.append(str(e))
        sync_status = "failed"

    completed = datetime.utcnow().isoformat()
    _last_sync = {
        "sync_id": sync_id,
        "status": sync_status,
        "started_at": now,
        "completed_at": completed,
        "rows_synced": rows_synced,
        "columns_synced": len(SHEETS_HEADERS),
        "errors": errors,
        "message": "Sync completed" if sync_status == "completed" else "Sync " + sync_status,
    }

    return SyncStatus(**_last_sync)
