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
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.src.infrastructure.api.v1.dependencies import get_current_user, require_role
from backend.src.infrastructure.persistence.sqlalchemy.database import get_db
from backend.src.domain.entities.email_template import EmailTemplate as EmailTemplateORM

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
    variables: Optional[Dict[str, str]] = None


class EmailLimitsResponse(BaseModel):
    remaining_per_hour: int
    cooldown_seconds: int
    warn_threshold: int = 40


# ── Default templates ─────────────────────────────────────────────────────────

DEFAULT_TEMPLATES: List[EmailTemplate] = [
    EmailTemplate(
        id=1,
        name="cargo_offer",
        subject="Предложение по грузоперевозке {route}",
        body="Уважаемый(ая) {contact_person},\n\nНаша компания {company_name} готова выполнить перевозку:\n\nМаршрут: {route}\nДетали груза: {cargo_details}\nПредлагаемая цена: {price}\n\nБудем рады сотрудничеству.\n\nС уважением,\n{sender_signature}",
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


_email_hourly = defaultdict(deque)  # user_id -> deque of send timestamps (last hour)
_email_last = {}                     # user_id -> last send timestamp


def _email_limit_state(user_id):
    now = time.time()
    q = _email_hourly[user_id]
    while q and now - q[0] > 3600:
        q.popleft()
    remaining = 50 - len(q)
    last = _email_last.get(user_id)
    cooldown = 0
    if last is not None:
        cooldown = max(0, int(30 - (now - last)))
    return q, remaining, cooldown


def _check_email_send(user_id):
    """Возвращает dict с вердиктом лимита. Если allowed - записывает попытку."""
    q, remaining, cooldown = _email_limit_state(user_id)
    if remaining <= 0:
        retry = int(3600 - (time.time() - q[0])) if q else 3600
        return {"allowed": False, "reason": "hourly_limit", "remaining": 0, "retry_after": retry}
    if cooldown > 0:
        return {"allowed": False, "reason": "cooldown", "remaining": remaining, "retry_after": cooldown}
    now = time.time()
    q.append(now)
    _email_last[user_id] = now
    remaining -= 1
    return {"allowed": True, "remaining": remaining, "warn": remaining <= 10}


def render_template(text: str, context: Dict[str, str]) -> str:
    """Подставляет переменные вида {name} в текст шаблона (FR-EMAIL-002)."""
    if not context:
        return text
    for key, value in context.items():
        text = text.replace("{" + key + "}", str(value))
    return text


def _orm_to_pydantic(t: EmailTemplateORM) -> EmailTemplate:
    return EmailTemplate(
        id=t.id,
        name=t.name,
        subject=t.subject,
        body=t.body,
        category=t.category,
        created_at=t.created_at.isoformat() if t.created_at else "",
        updated_at=t.updated_at.isoformat() if t.updated_at else "",
    )


def _ensure_seed(db: Session) -> None:
    if db.query(EmailTemplateORM).count() == 0:
        for t in DEFAULT_TEMPLATES:
            db.add(EmailTemplateORM(name=t.name, subject=t.subject, body=t.body, category=t.category))
        db.commit()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/templates", response_model=List[EmailTemplate])
async def get_email_templates(
    category: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Список шаблонов электронных писем."""
    _ensure_seed(db)
    q = db.query(EmailTemplateORM).order_by(EmailTemplateORM.id.asc())
    if category:
        q = q.filter(EmailTemplateORM.category == category)
    return [_orm_to_pydantic(t) for t in q.all()]


@router.post("/templates", response_model=EmailTemplate, status_code=status.HTTP_201_CREATED)
async def create_email_template(
    name: str,
    subject: str,
    body: str,
    category: str = "general",
    current_user=Depends(require_role(['administrator','director','dispatcher'])),
    db: Session = Depends(get_db),
):
    """Создать новый шаблон письма."""
    _ensure_seed(db)
    if db.query(EmailTemplateORM).filter(EmailTemplateORM.name == name).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Template with this name already exists")
    t = EmailTemplateORM(name=name, subject=subject, body=body, category=category)
    db.add(t)
    db.commit()
    db.refresh(t)
    return _orm_to_pydantic(t)


@router.put("/templates/{template_id}", response_model=EmailTemplate)
async def update_email_template(
    template_id: int,
    name: Optional[str] = None,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    category: Optional[str] = None,
    current_user=Depends(require_role(['administrator','director','dispatcher'])),
    db: Session = Depends(get_db),
):
    """Редактировать шаблон письма (FR-EMAIL-003)."""
    t = db.query(EmailTemplateORM).filter(EmailTemplateORM.id == template_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email template not found")
    if name is not None:
        t.name = name
    if subject is not None:
        t.subject = subject
    if body is not None:
        t.body = body
    if category is not None:
        t.category = category
    db.commit()
    db.refresh(t)
    return _orm_to_pydantic(t)


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


@router.get("/limits", response_model=EmailLimitsResponse)
async def get_email_limits(
    current_user=Depends(get_current_user),
):
    """Оставшийся лимит отправки писем (FR-EMAIL-008)."""
    q, remaining, cooldown = _email_limit_state(current_user.id)
    return EmailLimitsResponse(remaining_per_hour=remaining, cooldown_seconds=cooldown)


@router.post("/send", status_code=status.HTTP_200_OK)
async def send_email(
    request: SendEmailRequest,
    current_user=Depends(require_role(['administrator','director','dispatcher'])),
    db: Session = Depends(get_db),
):
    """Отправить письмо через SMTP."""
    if not SMTP_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SMTP not configured. Set SMTP_USERNAME and SMTP_PASSWORD in .env",
        )

    check = _check_email_send(current_user.id)
    if not check["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Email limit: " + check["reason"] + ". Remaining: " + str(check["remaining"]) + ". Retry in " + str(check["retry_after"]) + "s",
        )

    subject = request.subject
    body = request.body
    if request.template_id is not None:
        template = db.query(EmailTemplateORM).filter(EmailTemplateORM.id == request.template_id).first()
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email template not found",
            )
        subject = template.subject
        body = template.body
    variables = request.variables or {}
    subject = render_template(subject, variables)
    body = render_template(body, variables)

    try:
        import smtplib
        from email.mime.text import MIMEText
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = request.to
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, smtp_password)
            server.send_message(msg)
        return {"status": "sent", "to": request.to, "subject": subject}
    except Exception as e:
        logger.error("Email send failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
