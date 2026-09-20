"""
Domain Entity: VehiclePosition

Запись в истории перемещений ТС (GPS позиция, FR-GPS-004).
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.domain.entities.user import Base


class VehiclePosition(Base):
    __tablename__ = "vehicle_positions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vehicles.id", name="fk_vehicle_positions_vehicle_id"),
        nullable=False,
        index=True,
    )

    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    place_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    measured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<VehiclePosition(id={self.id}, vehicle_id={self.vehicle_id}, "
            f"place='{self.place_name}')>"
        )
