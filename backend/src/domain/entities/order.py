"""
Domain Entity: Order

Сущность заказа (фактического выполнения перевозки).
"""
import uuid
from datetime import date, datetime
from sqlalchemy import Float, Integer, Date, DateTime, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from backend.src.domain.entities.user import Base
import enum

class OrderStatus(enum.Enum):
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True)
    cargo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cargos.id", ondelete="SET NULL"), nullable=True)
    
    # Фактические показатели
    revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    margin: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    distance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    
    # Даты
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=OrderStatus.COMPLETED
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, vehicle_id={self.vehicle_id}, revenue={self.revenue})>"
