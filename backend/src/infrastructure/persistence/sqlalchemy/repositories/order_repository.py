"""
SQLAlchemy Implementation of OrderRepository
"""
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session

from backend.src.domain.entities.order import Order
from backend.src.domain.repositories.order_repository import OrderRepository

class SqlAlchemyOrderRepository(OrderRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, order_id: int) -> Optional[Order]:
        return self.session.query(Order).filter(Order.id == order_id).first()

    def get_all_for_vehicle(self, vehicle_id: int, start: date, end: date) -> List[Order]:
        return self.session.query(Order).filter(
            Order.vehicle_id == vehicle_id,
            Order.start_date >= start,
            Order.end_date <= end
        ).all()

    def save(self, order: Order) -> Order:
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        return order
