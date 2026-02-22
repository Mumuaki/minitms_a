"""
Domain Entity: Vehicle

Сущность транспортного средства.
"""
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.domain.entities.user import Base

class VehicleStatus(enum.Enum):
    """Статусы транспортного средства."""
    FREE = "Free"
    IN_TRANSIT = "In Transit"
    MAINTENANCE = "Maintenance"
    UNAVAILABLE = "Unavailable"

class VehicleType(enum.Enum):
    """Типы транспортных средств."""
    TENT = "Tent"
    REEFER = "Reefer"
    CONTAINER = "Container"
    OTHER = "Other"

class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    license_plate: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    
    vehicle_type: Mapped[VehicleType] = mapped_column(
        SQLEnum(VehicleType, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=VehicleType.TENT
    )
    
    # Dimensions in meters
    length: Mapped[float] = mapped_column(Float, nullable=False)
    width: Mapped[float] = mapped_column(Float, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Payload in kg
    payload_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    
    status: Mapped[VehicleStatus] = mapped_column(
        SQLEnum(VehicleStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=VehicleStatus.FREE
    )
    
    # GPS Info
    gps_tracker_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    current_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # e.g. "lat,lon"
    gps_last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Vehicle(id={self.id}, plate='{self.license_plate}', status={self.status.value})>"
