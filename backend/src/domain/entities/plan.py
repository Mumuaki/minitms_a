"""
Domain Entity: FinancialPlan

Сущность финансового плана транспортного средства.
"""
from datetime import date, datetime
from sqlalchemy import Float, Integer, Date, DateTime, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.src.domain.entities.user import Base


class FinancialPlan(Base):
    __tablename__ = "financial_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Период планирования
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Плановые показатели
    revenue_target: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    margin_target: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    distance_target: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    
    # Валюта плана (например, 'EUR')
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Отношения
    # vehicle = relationship("Vehicle", backref="financial_plans")

    def __repr__(self) -> str:
        return f"<FinancialPlan(id={self.id}, vehicle_id={self.vehicle_id}, period={self.period_start} to {self.period_end})>"
