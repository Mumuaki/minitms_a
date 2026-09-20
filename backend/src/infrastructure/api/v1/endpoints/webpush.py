"""Web-Push notification endpoints (FR-NOTIFY-001)."""
import base64
import logging
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

from backend.src.infrastructure.api.v1.dependencies import get_current_user, CurrentUser
from backend.src.infrastructure.persistence.sqlalchemy.database import get_db
from backend.src.domain.entities.app_setting import AppSetting
from backend.src.domain.entities.push_subscription import PushSubscription
from backend.src.infrastructure.external_services.webpush.web_push_service import WebPushService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications/webpush", tags=["Notifications"])

_PRIV_KEY = "webpush_vapid_private_key"
_PUB_KEY = "webpush_vapid_public_key"


def _generate_vapid_keys():
    priv = ec.generate_private_key(ec.SECP256R1())
    pub = priv.public_key()
    priv_pem = priv.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    raw_pub = pub.public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    pub_b64url = base64.urlsafe_b64encode(raw_pub).rstrip(b"=").decode()
    return priv_pem, pub_b64url


def _read_value(db: Session, key: str):
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if row and isinstance(row.value, dict):
        return row.value.get("v")
    return None


def _write_value(db: Session, key: str, val: str):
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if row:
        row.value = {"v": val}
    else:
        db.add(AppSetting(key=key, value={"v": val}))
    db.commit()


def _get_vapid_keys(db: Session):
    priv = _read_value(db, _PRIV_KEY)
    pub = _read_value(db, _PUB_KEY)
    if not priv or not pub:
        priv, pub = _generate_vapid_keys()
        _write_value(db, _PRIV_KEY, priv)
        _write_value(db, _PUB_KEY, pub)
    return priv, pub


def _send_to_user(db: Session, user_id: int, title: str, body: str) -> int:
    priv, _ = _get_vapid_keys(db)
    service = WebPushService(priv)
    subs = db.query(PushSubscription).filter(PushSubscription.user_id == user_id).all()
    sent = 0
    for s in subs:
        if service.send(s.subscription, title, body):
            sent += 1
    return sent


class PublicKeyResponse(BaseModel):
    public_key: str


class SubscribeRequest(BaseModel):
    subscription: Dict[str, Any]


class UnsubscribeRequest(BaseModel):
    endpoint: str


class TestSendResponse(BaseModel):
    status: str
    count: int


@router.get("/public-key", response_model=PublicKeyResponse)
def get_public_key(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    _, pub = _get_vapid_keys(db)
    return PublicKeyResponse(public_key=pub)


@router.post("/subscribe", status_code=201)
def subscribe(
    req: SubscribeRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    sub_data = req.subscription or {}
    endpoint = sub_data.get("endpoint")
    if not endpoint:
        raise HTTPException(status_code=400, detail="subscription.endpoint is required")
    existing = db.query(PushSubscription).filter(PushSubscription.endpoint == endpoint).first()
    if existing:
        existing.user_id = current_user.id
        existing.subscription = sub_data
        db.commit()
        return {"status": "subscribed", "id": existing.id}
    sub = PushSubscription(user_id=current_user.id, endpoint=endpoint, subscription=sub_data)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return {"status": "subscribed", "id": sub.id}


@router.delete("/subscribe")
def unsubscribe(
    req: UnsubscribeRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    sub = db.query(PushSubscription).filter(
        PushSubscription.endpoint == req.endpoint,
        PushSubscription.user_id == current_user.id,
    ).first()
    if sub:
        db.delete(sub)
        db.commit()
    return {"status": "unsubscribed"}


@router.post("/test", response_model=TestSendResponse)
def send_test(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    subs = db.query(PushSubscription).filter(PushSubscription.user_id == current_user.id).all()
    if not subs:
        raise HTTPException(status_code=404, detail="No subscriptions for this user")
    count = _send_to_user(db, current_user.id, "MiniTMS", "Тестовое push-уведомление")
    return TestSendResponse(status="sent", count=count)
