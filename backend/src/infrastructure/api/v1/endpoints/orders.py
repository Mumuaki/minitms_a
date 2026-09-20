"""
Orders Endpoints — создание и просмотр заказов (фактическое выполнение перевозки).
"""
import uuid
from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.src.infrastructure.persistence.sqlalchemy.database import get_db
from backend.src.infrastructure.api.v1.dependencies import get_current_user, require_role
from backend.src.domain.entities.order import Order, OrderStatus


router = APIRouter(prefix="/orders", tags=["Orders"])


class OrderCreate(BaseModel):
    vehicle_id: Optional[int] = None
    cargo_id: Optional[str] = None
    revenue: float = 0.0
    margin: float = 0.0
    distance: float = 0.0
    start_date: date
    end_date: date
    status: str = "Completed"


class OrderResponse(BaseModel):
    id: int
    vehicle_id: Optional[int] = None
    cargo_id: Optional[str] = None
    revenue: float
    margin: float
    distance: float
    start_date: date
    end_date: date
    status: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


def _to_response(o: Order) -> OrderResponse:
    return OrderResponse(
        id=o.id,
        vehicle_id=o.vehicle_id,
        cargo_id=str(o.cargo_id) if o.cargo_id else None,
        revenue=o.revenue,
        margin=o.margin,
        distance=o.distance,
        start_date=o.start_date,
        end_date=o.end_date,
        status=o.status.value if hasattr(o.status, "value") else o.status,
        created_at=o.created_at.isoformat() if o.created_at else None,
    )


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["administrator", "director", "dispatcher"])),
):
    valid = {s.value for s in OrderStatus}
    if payload.status not in valid:
        raise HTTPException(status_code=400, detail="Invalid status. Allowed: " + str(sorted(valid)))
    order = Order(
        vehicle_id=payload.vehicle_id,
        cargo_id=uuid.UUID(payload.cargo_id) if payload.cargo_id else None,
        revenue=payload.revenue,
        margin=payload.margin,
        distance=payload.distance,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=OrderStatus(payload.status),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return _to_response(order)


@router.get("/", response_model=List[OrderResponse])
def list_orders(
    vehicle_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    q = db.query(Order)
    if vehicle_id is not None:
        q = q.filter(Order.vehicle_id == vehicle_id)
    orders = q.order_by(Order.created_at.desc()).all()
    return [_to_response(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _to_response(order)


@router.delete("/{order_id}")
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["administrator", "director"])),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(order)
    db.commit()
    return {"status": "deleted", "order_id": order_id}
