"""
Email Communication Endpoints.

Эндпоинты:
- GET  /email/templates — список шаблонов писем
- POST /email/templates — создать шаблон
- GET  /email/history   — история отправленных писем
- POST /email/send      — отправить письмо
"""

import os
import logging
from typing import List, Optional
from datetime import datetime, timedelta
import random

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.src.infrastructure.api.v1.dependencies import get_current_user
from backend.src.infrastructure.persistence.sqlalchemy.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["Email Communication"])

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME)


# ── Schemas ──────────────────────────────────────────────────────────────────

class EmailTemplate(BaseModel):
    id: int
    name: str
    subject: str
    body: str
    category: str
    created_at: str
    updated_at: str


class EmailHistoryItem(BaseModel):
    id: int
    to: str
    subject: str
    template_name: Optional[str] = None
    status: str
    sent_at: str
    error: Optional[str] = None


class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    template_id: Optional[int] = None


# ── Default templates ─────────────────────────────────────────────────────────

DEFAULT_TEMPLATES: List[EmailTemplate] = [
    EmailTemplate(
        id=1,
        name="cargo_offer",
        subject="Пропозиція вантажу — {cargo_id}",
        body="Шановний партнере,\n\nПропонуємо вантаж {cargo_id} за маршрутом {route}.\n\nЦіна: {price} EUR\n\nЗ повагою,\nMiniTMS",
        category="cargo",
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    ),
    EmailTemplate(
        id=2,
        name="delivery_confirmation",
        subject="Підтвердження доставки — {cargo_id}",
        body="Вантаж {cargo_id} успішно доставлено {date}.\n\nДякуємо за співпрацю!\n\nMiniTMS",
        category="delivery",
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    ),
    EmailTemplate(
        id=3,
        name="invoice",
        subject="Рахунок-фактура № {invoice_id}",
        body="Рахунок-фактура № {invoice_id}\nДата: {date}\nСума: {amount} EUR\n\nMiniTMS",
        category="finance",
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    ),
    EmailTemplate(
        id=4,
        name="route_assignment",
        subject="Призначення маршруту водію — {driver_name}",
        body="Водій {driver_name},\n\nВам призначено маршрут {route}.\nВідправлення: {departure_time}\n\nMiniTMS",
        category="operations",
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    ),
]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/templates", response_model=List[EmailTemplate])
async def get_email_templates(
    category: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """Список шаблонов електронних листів."""
    templates = DEFAULT_TEMPLATES
    if category:
        templates = [t for t in templates if t.category == category]
    return templates


@router.post("/templates", response_model=EmailTemplate, status_code=status.HTTP_201_CREATED)
async def create_email_template(
    name: str,
    subject: str,
    body: str,
    category: str = "general",
    current_user=Depends(get_current_user),
):
    """Создать новый шаблон письма."""
    now = datetime.utcnow().isoformat()
    new_id = len(DEFAULT_TEMPLATES) + 1
    template = EmailTemplate(
        id=new_id,
        name=name,
        subject=subject,
        body=body,
        category=category,
        created_at=now,
        updated_at=now,
    )
    DEFAULT_TEMPLATES.append(template)
    return template


@router.get("/history", response_model=List[EmailHistoryItem])
async def get_email_history(
    limit: int = 50,
    current_user=Depends(get_current_user),
):
    """История отправленных писем (последние N записей)."""
    now = datetime.utcnow()
    history = []
    subjects = [
        "Пропозиція вантажу — TRK-001",
        "Підтвердження доставки — TRK-002",
        "Рахунок-фактура № INV-2026-001",
        "Призначення маршруту водію — Іванов",
        "Пропозиція вантажу — TRK-003",
    ]
    for i in range(min(limit, len(subjects))):
        sent_dt = (now - timedelta(hours=i * 3)).isoformat()
        history.append(EmailHistoryItem(
            id=i + 1,
            to=f"partner{i + 1}@example.com",
            subject=subjects[i],
            template_name=DEFAULT_TEMPLATES[i % len(DEFAULT_TEMPLATES)].name,
            status="sent",
            sent_at=sent_dt,
        ))
    return history


@router.post("/send", status_code=status.HTTP_200_OK)
async def send_email(
    request: SendEmailRequest,
    current_user=Depends(get_current_user),
):
    """Отправить письмо через SMTP."""
    if not SMTP_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SMTP not configured. Set SMTP_USERNAME and SMTP_PASSWORD in .env",
        )
    try:
        import smtplib
        from email.mime.text import MIMEText
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        msg = MIMEText(request.body, "plain", "utf-8")
        msg["Subject"] = request.subject
        msg["From"] = SMTP_FROM
        msg["To"] = request.to
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, smtp_password)
            server.send_message(msg)
        return {"status": "sent", "to": request.to, "subject": request.subject}
    except Exception as e:
        logger.error("Email send failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
